import os
import sqlite3
import json
from typing import List, Dict, Optional, Iterable, Tuple
import numpy as np

class Memory:
    def __init__(self, db_path: str = "./data/assistant.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        # Ensure foreign key cascades are enforced in SQLite for this connection
        try:
            self.conn.execute("PRAGMA foreign_keys = ON")
        except Exception:
            pass
        self._ensure()

    def _ensure(self):
        c = self.conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL, -- user|assistant|note|doc
                text TEXT NOT NULL,
                meta TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                vector TEXT NOT NULL,
                FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE CASCADE
            );
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS feedbacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                answer_id INTEGER,
                rating INTEGER, -- -1,0,1
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE SET NULL,
                FOREIGN KEY(answer_id) REFERENCES messages(id) ON DELETE SET NULL
            );
            """
        )
        self.conn.commit()

    def add(self, text: str, kind: str = "note", embedding: List[float] = None, meta: Dict = None) -> int:
        c = self.conn.cursor()
        c.execute("INSERT INTO messages (kind, text, meta) VALUES (?,?,?)", (kind, text, json.dumps(meta or {})))
        mid = c.lastrowid
        if embedding is not None:
            c.execute("INSERT INTO embeddings (message_id, vector) VALUES (?,?)", (mid, json.dumps(embedding)))
        self.conn.commit()
        return mid

    def index_text(self, text: str, vector: List[float], kind: str = "doc", meta: Dict = None) -> int:
        return self.add(text=text, kind=kind, embedding=vector, meta=meta)

    def search(self, query_vec: List[float], top_k: int = 5, kinds: Optional[List[str]] = None) -> List[Dict]:
        c = self.conn.cursor()
        if kinds:
            placeholders = ",".join(["?"] * len(kinds))
            c.execute(
                f"SELECT m.id, m.text, m.meta, e.vector FROM messages m JOIN embeddings e ON m.id = e.message_id WHERE m.kind IN ({placeholders})",
                kinds,
            )
        else:
            c.execute("SELECT m.id, m.text, m.meta, e.vector FROM messages m JOIN embeddings e ON m.id = e.message_id")
        rows = c.fetchall()
        if not rows:
            return []
        q = np.array(query_vec, dtype=float)
        scored = []
        for mid, text, meta, vec_json in rows:
            v = np.array(json.loads(vec_json), dtype=float)
            sim = float(np.dot(q, v) / (np.linalg.norm(q) * np.linalg.norm(v) + 1e-8))
            scored.append((sim, {"id": mid, "text": text, "meta": json.loads(meta or '{}')}))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:top_k]]

    def search_dense_with_scores(self, query_vec: List[float], top_k: int = 5, kinds: Optional[List[str]] = None) -> List[Dict]:
        """Like search(), but returns scores for blending: [{id,text,meta,score}]"""
        c = self.conn.cursor()
        if kinds:
            placeholders = ",".join(["?"] * len(kinds))
            c.execute(
                f"SELECT m.id, m.text, m.meta, e.vector FROM messages m JOIN embeddings e ON m.id = e.message_id WHERE m.kind IN ({placeholders})",
                kinds,
            )
        else:
            c.execute("SELECT m.id, m.text, m.meta, e.vector FROM messages m JOIN embeddings e ON m.id = e.message_id")
        rows = c.fetchall()
        if not rows:
            return []
        q = np.array(query_vec, dtype=float)
        out = []
        for mid, text, meta, vec_json in rows:
            v = np.array(json.loads(vec_json), dtype=float)
            sim = float(np.dot(q, v) / (np.linalg.norm(q) * np.linalg.norm(v) + 1e-8))
            out.append({"id": mid, "text": text, "meta": json.loads(meta or '{}'), "score": sim})
        out.sort(key=lambda x: x["score"], reverse=True)
        return out[:top_k]

    def list_docs(self) -> List[Dict]:
        """Return all doc messages [{id,text,meta}] without vectors (for sparse retrieval)."""
        c = self.conn.cursor()
        c.execute("SELECT id, text, meta FROM messages WHERE kind='doc'")
        rows = c.fetchall()
        return [{"id": mid, "text": text, "meta": json.loads(meta or '{}')} for (mid, text, meta) in rows]

    def bulk_index(self, items: Iterable[Tuple[str, List[float], Dict]] , kind: str = "doc") -> int:
        """Index multiple text chunks with precomputed vectors and metadata. Returns count indexed."""
        c = self.conn.cursor()
        count = 0
        for text, vector, meta in items:
            c.execute("INSERT INTO messages (kind, text, meta) VALUES (?,?,?)", (kind, text, json.dumps(meta or {})))
            mid = c.lastrowid
            c.execute("INSERT INTO embeddings (message_id, vector) VALUES (?,?)", (mid, json.dumps(vector)))
            count += 1
        self.conn.commit()
        return count

    def delete_docs_by_text_substring(self, snippet: str) -> int:
        """Delete documents where text contains the snippet (case-insensitive). Returns rows deleted."""
        c = self.conn.cursor()
        # Find matching message ids first (kind='doc')
        c.execute("SELECT id, text FROM messages WHERE kind='doc'")
        ids = [mid for (mid, text) in c.fetchall() if snippet.lower() in (text or '').lower()]
        if not ids:
            return 0
        c.executemany("DELETE FROM messages WHERE id = ?", [(mid,) for mid in ids])
        self.conn.commit()
        return len(ids)

    def delete_docs_by_source(self, source: str) -> int:
        """Delete documents where meta.source equals the provided source. Returns rows deleted."""
        c = self.conn.cursor()
        c.execute("SELECT id, meta FROM messages WHERE kind='doc'")
        ids = []
        for mid, meta in c.fetchall():
            try:
                m = json.loads(meta or '{}')
            except Exception:
                m = {}
            if str(m.get('source', '')).lower() == source.lower():
                ids.append(mid)
        if not ids:
            return 0
        c.executemany("DELETE FROM messages WHERE id = ?", [(mid,) for mid in ids])
        self.conn.commit()
        return len(ids)

    def delete_all_docs(self) -> int:
        """Delete all documents (kind='doc'). Returns rows deleted."""
        c = self.conn.cursor()
        c.execute("SELECT COUNT(1) FROM messages WHERE kind='doc'")
        n = c.fetchone()[0] or 0
        c.execute("DELETE FROM messages WHERE kind='doc'")
        self.conn.commit()
        return int(n)

    def add_feedback(self, message_id: int = None, answer_id: int = None, rating: int = 0, notes: str = "") -> int:
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO feedbacks (message_id, answer_id, rating, notes) VALUES (?,?,?,?)",
            (message_id, answer_id, rating, notes or "")
        )
        fid = c.lastrowid
        self.conn.commit()
        return fid

    def list_feedback(self, limit: int = 100) -> List[Dict]:
        c = self.conn.cursor()
        c.execute(
            "SELECT id, message_id, answer_id, rating, notes, created_at FROM feedbacks ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = c.fetchall()
        out = []
        for r in rows:
            out.append({
                "id": r[0],
                "message_id": r[1],
                "answer_id": r[2],
                "rating": r[3],
                "notes": r[4],
                "created_at": r[5],
            })
        return out

    def feedback_summary(self, answer_id: int) -> Dict:
        """Return counts for thumbs up/down and score for a given answer message id."""
        c = self.conn.cursor()
        c.execute(
            """
            SELECT 
                SUM(CASE WHEN rating > 0 THEN 1 ELSE 0 END) as up,
                SUM(CASE WHEN rating < 0 THEN 1 ELSE 0 END) as down,
                COUNT(1) as total
            FROM feedbacks
            WHERE answer_id = ?
            """,
            (answer_id,)
        )
        row = c.fetchone() or (0, 0, 0)
        up, down, total = [int(x or 0) for x in row]
        return {"up": up, "down": down, "total": total, "score": up - down}

    def export_dataset_jsonl(self) -> str:
        """Export minimal dataset as JSONL: {role, text}."""
        c = self.conn.cursor()
        c.execute("SELECT kind, text FROM messages ORDER BY id ASC")
        lines = []
        for kind, text in c.fetchall():
            role = "user" if kind == "user" else ("assistant" if kind == "assistant" else kind)
            lines.append({"role": role, "text": text})
        return "\n".join([json.dumps(l, ensure_ascii=False) for l in lines])
