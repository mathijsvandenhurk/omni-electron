from typing import List

try:
    from sentence_transformers import SentenceTransformer  # optional
except Exception:
    SentenceTransformer = None  # type: ignore


class Embeddings:
    """
    Embeddings helper with two backends:
    - sentence-transformers (if installed and selected)
    - sklearn HashingVectorizer fallback (default) to avoid heavy deps for initial runs

    Select backend via env EMBEDDINGS_BACKEND=st|sklearn (default: sklearn if ST not available).
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", backend: str | None = None):
        import os
        self.model_name = model_name
        env_backend = os.getenv("EMBEDDINGS_BACKEND")
        self.backend = (backend or env_backend or ("st" if SentenceTransformer else "sklearn")).lower()
        if self.backend == "st":
            if not SentenceTransformer:
                raise RuntimeError("sentence-transformers not installed. Set EMBEDDINGS_BACKEND=sklearn or install sentence-transformers.")
            self.model = SentenceTransformer(model_name)
            self.vectorizer = None
        else:
            from sklearn.feature_extraction.text import HashingVectorizer
            # HashingVectorizer requires no fitting and yields fixed-size vectors
            self.vectorizer = HashingVectorizer(n_features=512, alternate_sign=False, norm="l2")
            self.model = None

    def embed_text(self, text: str) -> List[float]:
        if self.backend == "st":
            v = self.model.encode([text], normalize_embeddings=True)[0]  # type: ignore[attr-defined]
            return v.tolist()
        else:
            mat = self.vectorizer.transform([text])  # type: ignore[union-attr]
            return mat.toarray()[0].tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if self.backend == "st":
            vs = self.model.encode(texts, normalize_embeddings=True)  # type: ignore[attr-defined]
            return [v.tolist() for v in vs]
        else:
            mat = self.vectorizer.transform(texts)  # type: ignore[union-attr]
            return mat.toarray().tolist()
