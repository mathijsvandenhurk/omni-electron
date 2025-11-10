"""
Omni Electron Backend - JSON-RPC Bridge with Self-Modification Tools

This module provides a JSON-RPC server that communicates with Electron
via stdin/stdout. It handles chat requests and provides real code analysis tools.
"""

import sys
import json
import os
import logging
import threading
import time
import asyncio
from pathlib import Path
import re

# Setup logging to stderr (not stdout - that's for JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format='[Python Backend] %(levelname)s: %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

def send_progress(message: str):
    """Send progress update to frontend via stderr"""
    # Encode multi-line messages as a single line using JSON encoding
    # This ensures multi-line content is preserved but sent as one unit
    import json
    encoded_message = json.dumps(message)  # This handles escaping of newlines and quotes
    print(f"[PROGRESS] {encoded_message}", file=sys.stderr, flush=True)

def send_heartbeat():
    """Send heartbeat to keep connection alive"""
    print("⏱️", file=sys.stderr, flush=True)  # Silent heartbeat, no progress message

class HeartbeatManager:
    """Manages background heartbeat during long operations"""
    
    def __init__(self, interval: int = 20):
        self.interval = interval
        self.active = False
        self.thread = None
    
    def start(self):
        """Start heartbeat in background thread"""
        if self.active:
            return
        
        self.active = True
        self.thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop heartbeat"""
        self.active = False
        if self.thread:
            self.thread.join(timeout=1)
    
    def _heartbeat_loop(self):
        """Background heartbeat loop"""
        while self.active:
            time.sleep(self.interval)
            if self.active:  # Check again after sleep
                send_heartbeat()

# Global heartbeat manager
heartbeat = HeartbeatManager()

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.llm_client import LLMClient
from core.memory import Memory
from core.embeddings import Embeddings
from self_modify.ast_analyzer import ASTAnalyzer
import re
from self_modify.repo_scanner import RepoScanner
from streaming import StreamingResponseHandler, get_vs_code_style_system_prompt
from type_defs.events import ResponseMetadata


class OmniBackend:
    """Main backend with real self-modification tools"""
    
    def __init__(self):
        logger.info("Initializing Omni Backend...")
        
        # Directories
        self.data_dir = os.getenv("DATA_DIR", str(backend_dir / "data"))
        os.makedirs(self.data_dir, exist_ok=True)
        self.project_root = backend_dir.parent
        
        # Core components
        self.memory = Memory(db_path=os.path.join(self.data_dir, "omni.db"))
        
        # Lazy-load embeddings (only when needed, using fast sklearn backend)
        self._embeddings = None
    
    @property
    def embeddings(self):
        """Lazy-load embeddings on first use"""
        if self._embeddings is None:
            # Use sklearn backend for fast startup (no model download)
            self._embeddings = Embeddings(
                model_name=os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
                backend="sklearn"  # Fast startup, no model download
            )
        return self._embeddings
    
    def _init_tools_and_llm(self):
        """Initialize tools and LLM (called after __init__)"""
        # Self-modification tools
        self.ast_analyzer = ASTAnalyzer()
        # Note: RepoScanner needs CodeIndexer, skip for now
        # self.repo_scanner = RepoScanner(indexer=...)
        
        # Available tools for Omni
        self.tools = {
            "read_file": self._tool_read_file,
            "write_file": self._tool_write_file,
            "list_files": self._tool_list_files,
            "search_in_file": self._tool_search_in_file,
            "replace_in_file": self._tool_replace_in_file,
        }
        
        # LLM client
        provider = os.getenv("LLM_PROVIDER", "anthropic")
        if provider == "anthropic":
            self.llm = LLMClient(
                provider="anthropic",
                api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
            )
        else:
            self.llm = LLMClient(
                provider="openai_compatible",
                api_base=os.getenv("LLM_API_BASE", "http://localhost:8001/v1"),
                api_key=os.getenv("LLM_API_KEY", "changeme"),
                model=os.getenv("LLM_MODEL", "llama3.3-70b-instruct")
            )
        
        logger.info(f"Backend ready: {provider}, model={self.llm.model}")
        
        # Initialize async client for better performance
        if provider == "anthropic":
            try:
                logger.info("🚀 Initializing async LLM client with connection pooling...")
                asyncio.run(self.llm.init_async())
            except Exception as e:
                logger.warning(f"⚠️  Async client initialization failed: {e}. Will use on-demand initialization.")
    
    def _tool_read_file(self, filepath: str) -> dict:
        """Read a file from the project"""
        try:
            full_path = self.project_root / filepath
            if not full_path.exists():
                return {"error": f"File not found: {filepath}"}
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "filepath": filepath,
                "content": content,
                "lines": len(content.split('\n'))
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _tool_write_file(self, filepath: str, content: str) -> dict:
        """Write content to a file"""
        try:
            full_path = self.project_root / filepath
            
            # Create backup
            if full_path.exists():
                backup_path = full_path.with_suffix(full_path.suffix + '.backup')
                with open(full_path, 'r', encoding='utf-8') as f:
                    with open(backup_path, 'w', encoding='utf-8') as bf:
                        bf.write(f.read())
            
            # Write new content
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "filepath": filepath,
                "message": f"File written successfully"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _tool_list_files(self, directory: str = ".") -> dict:
        """List files in a directory"""
        try:
            dir_path = self.project_root / directory
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory}"}
            
            files = []
            for item in dir_path.iterdir():
                files.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "path": str(item.relative_to(self.project_root))
                })
            
            return {
                "directory": directory,
                "files": files,
                "count": len(files)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _tool_search_in_file(self, filepath: str, pattern: str) -> dict:
        """Search for a pattern in a file"""
        try:
            full_path = self.project_root / filepath
            if not full_path.exists():
                return {"error": f"File not found: {filepath}"}
            
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            matches = []
            for i, line in enumerate(lines, 1):
                if pattern.lower() in line.lower():
                    matches.append({
                        "line_number": i,
                        "content": line.strip()
                    })
            
            return {
                "filepath": filepath,
                "pattern": pattern,
                "matches": matches,
                "count": len(matches)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _tool_replace_in_file(self, filepath: str, old_text: str, new_text: str) -> dict:
        """Replace text in a file (safer than rewriting entire file)"""
        try:
            full_path = self.project_root / filepath
            if not full_path.exists():
                return {"error": f"File not found: {filepath}"}
            
            # Read current content
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if old_text exists
            if old_text not in content:
                return {
                    "error": f"Text not found in file. Make sure the old_text matches exactly.",
                    "searched_for": old_text[:100]
                }
            
            # Create backup
            backup_path = full_path.with_suffix(full_path.suffix + '.backup')
            with open(backup_path, 'w', encoding='utf-8') as bf:
                bf.write(content)
            
            # Replace and write
            new_content = content.replace(old_text, new_text)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return {
                "success": True,
                "filepath": filepath,
                "replacements": content.count(old_text),
                "message": f"Replaced {content.count(old_text)} occurrence(s)"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _execute_tool(self, tool_name: str, params: dict) -> dict:
        """Execute a tool by name"""
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            return self.tools[tool_name](**params)
        except Exception as e:
            logger.error(f"Tool {tool_name} error: {e}")
            return {"error": str(e)}
    
    def _emit_event(self, event: dict):
        """Emit streaming event to frontend via JSON-RPC on stdout"""
        # Wrap event in JSON-RPC notification format
        notification = {
            "jsonrpc": "2.0",
            "method": "chat_event",
            "params": event
        }
        print(json.dumps(notification), flush=True)
    
    async def chat_streaming(self, params: dict) -> dict:
        """
        Handle chat with streaming responses and real-time event emission.
        This replaces the old multi-LLM-call approach with a single streaming call.
        Uses async I/O for 24-36x faster response times.
        """
        message = params.get("message", "").strip()
        request_id = params.get("request_id", f"req_{int(time.time() * 1000)}")
        
        if not message:
            return {"answer": "Please provide a message."}
        
        logger.info(f"[Streaming Chat] Request ID: {request_id}, Message: {message[:50]}...")
        
        # Create streaming handler
        handler = StreamingResponseHandler(
            request_id=request_id,
            emit_callback=self._emit_event
        )
        
        try:
            # Emit response start
            handler.emit_response_start()
            
            # Get available tools
            tools = [
                {
                    "name": "read_file",
                    "description": "Lees een bestand uit het project. Returns file content.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "filepath": {"type": "string", "description": "Path to file relative to project root"}
                        },
                        "required": ["filepath"]
                    }
                },
                {
                    "name": "write_file",
                    "description": "Schrijf een NIEUW bestand. Use only for creating new files, not editing existing ones.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "filepath": {"type": "string", "description": "Path to new file"},
                            "content": {"type": "string", "description": "Full file content"}
                        },
                        "required": ["filepath", "content"]
                    }
                },
                {
                    "name": "replace_in_file",
                    "description": "GEBRUIK DEZE TOOL OM CODE TE WIJZIGEN! Vervang specifieke tekst in een bestand. Dit is de PRIMAIRE tool voor alle code edits, styling changes, en bug fixes. ALTIJD gebruiken wanneer de user vraagt iets te veranderen!",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "filepath": {"type": "string", "description": "Path to file"},
                            "old_text": {"type": "string", "description": "Exact text to replace"},
                            "new_text": {"type": "string", "description": "New text"}
                        },
                        "required": ["filepath", "old_text", "new_text"]
                    }
                },
                {
                    "name": "search_in_file",
                    "description": "Zoek tekst pattern in een bestand",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "filepath": {"type": "string", "description": "Path to file"},
                            "pattern": {"type": "string", "description": "Search pattern or regex"}
                        },
                        "required": ["filepath", "pattern"]
                    }
                },
                {
                    "name": "list_files",
                    "description": "Lijst bestanden in een directory",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "directory": {"type": "string", "description": "Directory path"}
                        },
                        "required": ["directory"]
                    }
                }
            ]
            
            # Get system prompt
            tools_desc = "\n".join([f"- {t['name']}: {t['description']}" for t in tools])
            system_prompt = get_vs_code_style_system_prompt(str(self.project_root), tools_desc)
            
            # Build conversation messages
            messages = [
                {
                    "role": "user",
                    "content": message
                }
            ]
            
            # Stream LLM response with tool calling
            # ADAPTIVE ITERATION LIMIT: Start with 5, extend dynamically if making progress
            max_iterations = 5
            max_extended_iterations = 12  # Safety ceiling (lowered from 15 to avoid rate limits)
            iteration = 0
            accumulated_text = ""
            write_tools_executed = set()  # Track if any write operations were performed
            read_tool_count = 0  # Track consecutive reads without writes
            
            while iteration < max_iterations:
                iteration += 1
                logger.info(f"[Streaming] Iteration {iteration}/{max_iterations}")
                
                # EARLY EXIT: If write operations were done and model responds without tools, we're done
                if iteration > 3 and write_tools_executed and not accumulated_text.endswith('...'):
                    logger.info(f"[Early exit] Write operations completed, stopping at iteration {iteration}")
                    break
                
                # NOTE: Tool choice forcing removed - caused 400 Bad Request errors
                # Instead, we rely on the guidance prompt injection (below) to redirect behavior
                
                # Stream from LLM (async)
                tool_uses = []
                current_tool_use = None
                current_text_block = ""
                assistant_content = []  # Build assistant message content
                
                async for event in self.llm.stream_with_tools(
                    messages=messages,
                    tools=tools,
                    max_tokens=4096,
                    temperature=0.7,
                    timeout=300
                ):
                    event_type = event.get('event_type', '')
                    
                    if event_type == 'message_start':
                        logger.debug("[Streaming] Message start")
                        
                    elif event_type == 'content_block_start':
                        content_block = event.get('content_block', {})
                        block_type = content_block.get('type')
                        
                        if block_type == 'text':
                            logger.debug("[Streaming] Text block start")
                            current_text_block = ""
                            
                        elif block_type == 'tool_use':
                            tool_name = content_block.get('name')
                            tool_id = content_block.get('id')
                            logger.info(f"[Streaming] Tool use start: {tool_name}")
                            
                            current_tool_use = {
                                'id': tool_id,
                                'name': tool_name,
                                'input': {}
                            }
                    
                    elif event_type == 'content_block_delta':
                        delta = event.get('delta', {})
                        delta_type = delta.get('type')
                        
                        if delta_type == 'text_delta':
                            text = delta.get('text', '')
                            current_text_block += text
                            accumulated_text += text
                            
                            # Emit narrative chunk
                            handler.emit_narrative_chunk(text, is_markdown=True)
                            
                        elif delta_type == 'input_json_delta':
                            # Tool parameter streaming
                            partial_json = delta.get('partial_json', '')
                            if current_tool_use:
                                # Accumulate JSON (we'll parse when complete)
                                if 'partial_json' not in current_tool_use:
                                    current_tool_use['partial_json'] = ''
                                current_tool_use['partial_json'] += partial_json
                    
                    elif event_type == 'content_block_stop':
                        if current_text_block:
                            logger.debug(f"[Streaming] Text block complete: {len(current_text_block)} chars")
                            # Add text block to assistant content
                            assistant_content.append({
                                "type": "text",
                                "text": current_text_block
                            })
                            current_text_block = ""
                            
                        if current_tool_use:
                            # Parse accumulated JSON
                            try:
                                if 'partial_json' in current_tool_use:
                                    current_tool_use['input'] = json.loads(current_tool_use['partial_json'])
                                    del current_tool_use['partial_json']
                            except json.JSONDecodeError as e:
                                logger.error(f"[Streaming] Failed to parse tool input JSON: {e}")
                                current_tool_use['input'] = {}
                            
                            # Add tool_use block to assistant content
                            assistant_content.append({
                                "type": "tool_use",
                                "id": current_tool_use['id'],
                                "name": current_tool_use['name'],
                                "input": current_tool_use['input']
                            })
                            
                            tool_uses.append(current_tool_use)
                            current_tool_use = None
                    
                    elif event_type == 'message_delta':
                        # Usage updates, stop_reason, etc.
                        pass
                    
                    elif event_type == 'message_stop':
                        logger.info("[Streaming] Message complete")
                        break
                
                # If no tools were called, we're done
                if not tool_uses:
                    logger.info("[Streaming] No tools called, response complete")
                    break
                
                # Add assistant message with complete content (text + tool_use blocks)
                messages.append({
                    "role": "assistant",
                    "content": assistant_content
                })
                logger.info(f"[Streaming] Added assistant message with {len(assistant_content)} blocks (text + tool_use)")
                
                # Execute tools and track progress
                tool_results = []
                for tool_use in tool_uses:
                    tool_name = tool_use['name']
                    tool_args = tool_use['input']
                    tool_id = tool_use['id']
                    
                    # Track tool types for adaptive iteration management
                    if tool_name in ['replace_in_file', 'write_file']:
                        write_tools_executed.add(tool_name)
                        read_tool_count = 0  # Reset read counter when we do a write
                    elif tool_name in ['read_file', 'search_in_file', 'list_files']:
                        read_tool_count += 1
                    
                    logger.info(f"[Streaming] Executing tool: {tool_name} with args: {tool_args}")
                    
                    # Emit tool start event
                    handler.emit_tool_start(tool_name, tool_args)
                    
                    # Execute tool
                    start_time = time.time()
                    try:
                        result = self._execute_tool(tool_name, tool_args)
                        duration = time.time() - start_time
                        
                        if result.get('error'):
                            status = 'error'
                            error_msg = result['error']
                            logger.error(f"[Streaming] Tool {tool_name} failed: {error_msg}")
                            handler.emit_tool_result(tool_name, result, status, duration, error=error_msg)
                        else:
                            status = 'success'
                            logger.info(f"[Streaming] Tool {tool_name} success in {duration:.2f}s")
                            handler.emit_tool_result(tool_name, result, status, duration)
                        
                        # Build tool result for next LLM call
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": json.dumps(result)
                        })
                        
                    except Exception as e:
                        duration = time.time() - start_time
                        error_msg = str(e)
                        logger.error(f"[Streaming] Tool {tool_name} exception: {error_msg}")
                        handler.emit_tool_result(tool_name, {'error': error_msg}, 'error', duration, error=error_msg)
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": json.dumps({"error": error_msg})
                        })
                
                # ADAPTIVE ITERATION EXTENSION: Extend limit if we're making progress toward task completion
                # Add tool results to conversation for next iteration
                # IMPORTANT: tool_results must go in a USER message, not assistant!
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
                
                # EARLY EXIT CONDITION: If we've done write operations and we're past iteration 4, check if we should stop
                # This prevents over-optimization (continuing to make small tweaks after task is complete)
                if iteration >= 4 and write_tools_executed:
                    logger.info(f"[Early exit check] {len(write_tools_executed)} write tool(s) executed. Giving model one more chance to confirm completion...")
                    # Let the model respond one more time to confirm completion or do final touches
                    # If it doesn't use tools, the "No tools called" check above will stop the loop
                
                # ADAPTIVE ITERATION EXTENSION: After adding tool results, check if we should extend
                # Pattern: Many reads followed by writes = analysis → implementation workflow
                if iteration == max_iterations - 1 and max_iterations < max_extended_iterations:
                    # Check if we're in "analysis phase" (many reads, no writes yet)
                    if read_tool_count >= 2 and not write_tools_executed:
                        logger.warning(f"[Adaptive] Detected analysis-only pattern ({read_tool_count} reads, 0 writes). Extending iterations by 5.")
                        max_iterations += 5
                        max_iterations = min(max_iterations, max_extended_iterations)  # Cap at safety limit
                        
                        # Inject guidance AFTER tool results (as separate user message)
                        # This keeps conversation valid: assistant (with tools) → user (tool results) → user (guidance)
                        # Note: Multiple consecutive user messages are allowed in Anthropic API
                        implementation_prompt = {
                            "role": "user",
                            "content": "Je hebt nu genoeg informatie verzameld via read/search tools. Focus nu op het IMPLEMENTEREN van de wijzigingen met replace_in_file. Maak de code changes die nodig zijn!"
                        }
                        messages.append(implementation_prompt)
            
            # Store in memory
            self.memory.add(text=message, kind="user")
            self.memory.add(text=accumulated_text, kind="assistant")
            
            # Emit response complete
            handler.emit_response_complete(tokens_used=0)  # TODO: track actual tokens
            
            logger.info(f"[Streaming] Response complete. Total text: {len(accumulated_text)} chars")
            return {"answer": accumulated_text, "request_id": request_id}
            
        except Exception as e:
            logger.error(f"[Streaming] Chat error: {e}", exc_info=True)
            
            # Parse error message for better user feedback
            error_str = str(e)
            user_message = error_str
            is_recoverable = False
            
            # Check for Anthropic API errors
            if "api_error" in error_str.lower() or "internal server error" in error_str.lower():
                user_message = "Anthropic API is tijdelijk niet beschikbaar. Probeer het over een paar seconden opnieuw."
                is_recoverable = True
            elif "rate_limit" in error_str.lower() or "429" in error_str:
                user_message = "Te veel verzoeken. Even wachten voordat je opnieuw probeert."
                is_recoverable = True
            elif "timeout" in error_str.lower():
                user_message = "Request timeout. Probeer het opnieuw met een kortere prompt."
                is_recoverable = True
            elif "authentication" in error_str.lower() or "api_key" in error_str.lower():
                user_message = "API key probleem. Check je ANTHROPIC_API_KEY environment variable."
                is_recoverable = False
            
            # Emit error event
            handler.emit_error(
                message=user_message,
                code="CHAT_ERROR",
                recoverable=is_recoverable
            )
            
            return {"answer": f"Error: {user_message}", "request_id": request_id}
    
    def chat(self, params: dict) -> dict:
        """Handle chat with multi-step tool execution support and smart timeout handling"""
        message = params.get("message", "").strip()
        if not message:
            return {"answer": "Please provide a message."}
        
        logger.info(f"Chat: {message[:50]}...")
        
        # Start heartbeat for long operations
        heartbeat.start()
        
        try:
            # Tools description
            tools_desc = """
BESCHIKBARE TOOLS:
1. read_file(filepath) - Lees een bestand uit het project
2. write_file(filepath, content) - Schrijf GEHEEL bestand (gebruik alleen voor nieuwe bestanden)
3. replace_in_file(filepath, old_text, new_text) - Vervang specifieke tekst (VOORKEUR voor edits!)
4. list_files(directory) - Lijst bestanden in een directory
5. search_in_file(filepath, pattern) - Zoek tekst in een bestand

TOOL GEBRUIK:
Om een tool te gebruiken, antwoord met:
<TOOL>tool_name</TOOL>
<PARAMS>{"param": "value"}</PARAMS>

Je kunt meerdere tools achter elkaar gebruiken!

TIP: Gebruik replace_in_file voor kleine wijzigingen (CSS, code edits)!
"""
            
            # Omni system prompt
            system_prompt = f"""Je bent Omni - een self-modifying AI desktop applicatie.

IDENTITEIT:
- Naam: Omni
- Type: Electron + Vue 3 + Python backend
- Locatie: {self.project_root}
- Engine: Claude (Anthropic)

ECHTE MOGELIJKHEDEN:
✅ Bestanden lezen en schrijven in dit project
✅ Code analyseren
✅ Jezelf modificeren (hot-reload)
✅ Styling aanpassen (CSS files)

{tools_desc}

KRITIEKE REGEL: Als de user vraagt iets te VERANDEREN → GEBRUIK METEEN TOOLS!
Zeg NOOIT "ik kan dit niet" - JE KUNT HET WEL!

Voor UI changes:
1. Search in src/components/ChatPanel.vue
2. Use replace_in_file om CSS te wijzigen
3. Klaar - hot-reload doet de rest!

WORKFLOW voor "Maak tekst cyaan":

"Ik ga de tekst cyaan maken! Even zoeken..."

<TOOL>search_in_file</TOOL><PARAMS>{{"filepath": "src/components/ChatPanel.vue", "pattern": "message-content"}}</PARAMS>

[Tool geeft regel nummer]

"Gevonden! Nu pas ik color: #d4d4d4 aan naar cyaan..."

<TOOL>replace_in_file</TOOL><PARAMS>{{"filepath": "src/components/ChatPanel.vue", "old_text": "  color: #d4d4d4;", "new_text": "  color: #00ffff;"}}</PARAMS>

"✅ Klaar! Check de app - het is nu cyaan!"

ONTHOUD: ACTIE > PRAATJES. Gebruik tools DIRECT!

RESPONSE STYLE (belangrijk):
- Schrijf als een natuurlijke assistent, geen gestructureerde lijsten
- Begin direct met de oplossing of analyse
- Noem bestanden kort: ChatPanel.vue niet volledige paden
- Gebruik emoji's alleen voor tool acties (📖 📝 ✅ ❌)
- Eindig met een relevante follow-up vraag indien passend
- NOOIT een "mijn proces" of samenvatting sectie aan het eind
- Praat zoals VS Code Copilot: vloeiend, direct, behulpzaam

GOED: "Ik zie het probleem in ChatPanel.vue. De kleur staat nog op #d4d4d4 en moet cyaan worden. Ik pas dat nu aan..."
FOUT: "**Stap 1:** Analyseer bestand\n**Stap 2:** Pas aan\n\n✨ Mijn proces:\n- Bestand gelezen\n- Wijziging toegepast"
"""
            
            # Multi-step tool execution loop with planning
            conversation_history = f"User: {message}\n\nOmni:"
            max_iterations = 5
            tool_results = []
            response = ""
            execution_plan = ""
            progress_log = []  # Keep track of all progress messages
            
            def log_progress(message: str, emoji: str = ""):
                """Send progress and keep log for final summary"""
                full_message = f"{emoji} {message}".strip() if emoji else message
                send_progress(full_message)
                progress_log.append(full_message)
            
            def send_heartbeat():
                """Send minimal heartbeat to prevent timeout"""
                try:
                    print("⏱️", file=sys.stderr, flush=True)  # Minimal heartbeat signal
                except:
                    pass
            
            for iteration in range(max_iterations):
                # First iteration: Generate plan and initial analysis
                if iteration == 0:
                    # Generate execution plan
                    planning_prompt = f"""Je bent Omni. De gebruiker vraagt: "{message}"

Maak een kort maar duidelijk plan van aanpak (max 3-4 zinnen):
1. Wat ga je precies doen?
2. Welke bestanden ga je bekijken/wijzigen?
3. In welke volgorde ga je te werk?

Schrijf alsof je tegen de gebruiker praat. Wees specifiek over bestandsnamen en acties."""
                    
                    try:
                        send_heartbeat()  # Heartbeat before LLM call
                        execution_plan = self.llm.generate(
                            prompt=planning_prompt,
                            max_tokens=200,
                            temperature=0.7
                        )
                        send_heartbeat()  # Heartbeat after LLM call
                        
                        # Send the execution plan in parts to ensure all content reaches the chat
                        full_plan_text = execution_plan.strip()
                        
                        # Split into paragraphs and send each as a separate progress message
                        # This ensures multi-line plans are fully transmitted
                        paragraphs = [p.strip() for p in full_plan_text.split('\n\n') if p.strip()]
                        
                        if paragraphs:
                            # First paragraph with the Plan: prefix
                            send_progress(f"📋 Plan: {paragraphs[0]}")
                            progress_log.append(f"📋 Plan: {paragraphs[0]}")
                            
                            # Additional paragraphs as continuation
                            for i, paragraph in enumerate(paragraphs[1:], 1):
                                send_progress(f"📋 {paragraph}")
                                progress_log.append(f"📋 {paragraph}")
                        else:
                            # Fallback if no paragraphs found
                            send_progress(f"📋 Plan: {full_plan_text}")
                            progress_log.append(f"📋 Plan: {full_plan_text}")
                    except Exception as e:
                        logger.warning(f"Failed to generate plan: {e}")
                        log_progress("Ik ga je vraag stap voor stap uitwerken...", "📋")
                    
                    log_progress("Ik begin nu met de uitvoering...", "🚀")
                
                # Generate response
                full_prompt = f"{system_prompt}\n\n{conversation_history}"
                send_heartbeat()  # Heartbeat before main LLM call
                response = self.llm.generate(
                    prompt=full_prompt,
                    max_tokens=2048,
                    temperature=0.9
                )
                send_heartbeat()  # Heartbeat after main LLM call
                
                # Check for tool calls
                tool_match = re.search(r'<TOOL>(.*?)</TOOL>', response)
                params_match = re.search(r'<PARAMS>(.*?)</PARAMS>', response, re.DOTALL)
                
                if tool_match and params_match:
                    tool_name = tool_match.group(1).strip()
                    try:
                        tool_params = json.loads(params_match.group(1))
                    except Exception as e:
                        logger.error(f"Failed to parse tool params: {e}")
                        tool_params = {}
                    
                    # Generate dynamic explanation of what Omni will do next
                    next_action_prompt = f"""Je bent Omni. Je gaat nu tool "{tool_name}" gebruiken met parameters: {json.dumps(tool_params, indent=2)}

Context: 
- Gebruiker vraagt: "{message}"
- Dit is stap {iteration + 1} van je plan
- Je hebt al {len(tool_results)} tool(s) gebruikt

Leg uit (1-2 zinnen) wat je nu precies gaat doen en waarom dit de logische volgende stap is.
Schrijf alsof je tegen de gebruiker praat."""
                    
                    # Emoji mapping for tools
                    emoji_map = {
                        "read_file": "📖",
                        "write_file": "✏️", 
                        "replace_in_file": "🔧",
                        "search_in_file": "🔍",
                        "list_files": "📂"
                    }
                    
                    try:
                        send_heartbeat()  # Heartbeat before explanation LLM call
                        next_action_explanation = self.llm.generate(
                            prompt=next_action_prompt,
                            max_tokens=150,
                            temperature=0.7
                        )
                        send_heartbeat()  # Heartbeat after explanation LLM call
                        
                        emoji = emoji_map.get(tool_name, "🔧")
                        # Send the full explanation, handling multi-line content
                        full_explanation = next_action_explanation.strip()
                        
                        # If it's multi-line, split into separate progress messages
                        if '\n' in full_explanation:
                            lines = [line.strip() for line in full_explanation.split('\n') if line.strip()]
                            for i, line in enumerate(lines):
                                send_progress(f"{emoji} {line}")
                                progress_log.append(f"{emoji} {line}")
                        else:
                            send_progress(f"{emoji} {full_explanation}")
                            progress_log.append(f"{emoji} {full_explanation}")
                    except Exception as e:
                        logger.warning(f"Failed to generate next action explanation: {e}")
                        # Fallback to enhanced templates
                        fallback_messages = {
                            "read_file": f"Ik ga {tool_params.get('filepath', 'het bestand')} lezen om de huidige situatie te begrijpen...",
                            "write_file": f"Ik ga een nieuw bestand {tool_params.get('filepath', '')} aanmaken met de benodigde functionaliteit...",
                            "replace_in_file": f"Ik ga de code in {tool_params.get('filepath', 'het bestand')} aanpassen om je wens te implementeren...",
                            "search_in_file": f"Ik ga in {tool_params.get('filepath', 'het bestand')} zoeken naar '{tool_params.get('pattern', 'de relevante code')}'...",
                            "list_files": f"Ik ga de bestanden in {tool_params.get('directory', 'de directory')} bekijken om de structuur te begrijpen..."
                        }
                        emoji = emoji_map.get(tool_name, "🔧")
                        log_progress(fallback_messages.get(tool_name, f"Ik ga tool {tool_name} gebruiken voor de volgende stap..."), emoji)
                    
                    logger.info(f"[Iteration {iteration+1}] Executing tool: {tool_name}")
                    tool_result = self._execute_tool(tool_name, tool_params)
                    tool_results.append({
                        "tool": tool_name,
                        "params": tool_params,
                        "result": tool_result
                    })
                    
                    # Generate intelligent result analysis and next step explanation
                    result_analysis_prompt = f"""Je bent Omni. Je hebt zojuist tool "{tool_name}" gebruikt.

Tool resultaat: {json.dumps(tool_result, indent=2)}

Context:
- Gebruiker vraagt: "{message}"
- Dit was stap {iteration + 1} van je plan
- Je hebt nu {len(tool_results)} stap(pen) voltooid

Leg uit (max 2 zinnen):
1. Wat je hebt bereikt met deze stap
2. Wat je logische volgende stap wordt (of dat je klaar bent)

Wees specifiek over wat je hebt gevonden/gedaan en waarom dat belangrijk is."""
                    
                    try:
                        send_heartbeat()  # Heartbeat before analysis LLM call
                        result_analysis = self.llm.generate(
                            prompt=result_analysis_prompt,
                            max_tokens=150,
                            temperature=0.7
                        )
                        send_heartbeat()  # Heartbeat after analysis LLM call
                        
                        # Choose emoji based on success/failure
                        if tool_result.get("success") or (tool_result.get("error") is None and tool_result.get("content")):
                            emoji = "✅"
                        elif tool_result.get("error"):
                            emoji = "❌"
                        else:
                            emoji = "ℹ️"
                        
                        send_progress(f"{emoji} {result_analysis.strip()}")
                        progress_log.append(f"{emoji} {result_analysis.strip()}")
                    except Exception as e:
                        logger.warning(f"Failed to generate result analysis: {e}")
                        # Enhanced fallback with more context
                        if tool_result.get("success") or (tool_result.get("error") is None and tool_result.get("content")):
                            if tool_name == "read_file" and tool_result.get("content"):
                                lines = tool_result.get("lines", 0)
                                log_progress(f"Bestand gelezen ({lines} regels). Ik ga nu de inhoud analyseren en de benodigde wijzigingen bepalen...", "✅")
                            elif tool_name == "write_file":
                                filepath = tool_result.get("filepath", "")
                                log_progress(f"Bestand {filepath} succesvol geschreven. Hot-reload zou actief moeten zijn en wijzigingen direct zichtbaar...", "✅")
                            elif tool_name == "replace_in_file":
                                replacements = tool_result.get("replacements", 0)
                                filepath = tool_result.get("filepath", "")
                                log_progress(f"{replacements} wijziging(en) in {filepath} doorgevoerd. De nieuwe functionaliteit is nu geïmplementeerd...", "✅")
                            elif tool_name == "search_in_file":
                                count = tool_result.get("count", 0)
                                log_progress(f"{count} match(es) gevonden. Ik weet nu waar ik de wijzigingen moet aanbrengen...", "✅")
                            elif tool_name == "list_files":
                                count = tool_result.get("count", 0)
                                log_progress(f"{count} bestanden/directories geanalyseerd. Ik begrijp nu de projectstructuur...", "✅")
                            else:
                                log_progress(f"{tool_name} voltooid! Ik ga verder met de volgende stap van het plan...", "✅")
                        elif tool_result.get("error"):
                            error_msg = str(tool_result.get('error', ''))[:50]
                            if "not found" in error_msg.lower():
                                log_progress("Bestand niet gevonden. Ik ga een alternatieve aanpak proberen en eerst de structuur verkennen...", "❌")
                            elif "text not found" in error_msg.lower():
                                log_progress("Tekst niet gevonden in bestand. Ik ga met een andere zoekstrategie proberen...", "❌")
                            else:
                                log_progress(f"Fout bij {tool_name}: {error_msg}. Ik ga een andere aanpak proberen...", "❌")
                        else:
                            log_progress(f"{tool_name} uitgevoerd. Ik ga door naar de volgende stap van het plan...", "ℹ️")
                    
                    # Update conversation with tool result
                    conversation_history += f"\n\n[Used {tool_name}]\nTool Result: {json.dumps(tool_result, indent=2)}\n\nOmni:"
                    
                    # Continue to next iteration to see if more tools needed
                    continue
                else:
                    # No more tools, generate intelligent final summary
                    if tool_results:
                        completion_summary_prompt = f"""Je bent Omni. Je hebt je plan uitgevoerd voor de vraag: "{message}"

Je hebt {len(tool_results)} stappen voltooid:
{chr(10).join([f"- {t['tool']}: {t['result'].get('filepath', t['result'].get('directory', 'uitgevoerd'))}" for t in tool_results])}

Geef een korte, enthousiaste samenvatting (max 2 zinnen):
1. Wat je hebt bereikt
2. Wat de gebruiker nu kan zien/doen

Vermeld specifiek of er bestanden zijn aangemaakt/gewijzigd en dat hot-reload actief is."""
                        
                        try:
                            send_heartbeat()  # Heartbeat before completion LLM call
                            completion_summary = self.llm.generate(
                                prompt=completion_summary_prompt,
                                max_tokens=150,
                                temperature=0.8
                            )
                            send_heartbeat()  # Heartbeat after completion LLM call
                            
                            # Send the completion summary, handling multi-line content
                            full_summary = completion_summary.strip()
                            
                            # If it's multi-line, split into separate progress messages
                            if '\n' in full_summary:
                                lines = [line.strip() for line in full_summary.split('\n') if line.strip()]
                                for line in lines:
                                    send_progress(f"✨ {line}")
                                    progress_log.append(f"✨ {line}")
                            else:
                                send_progress(f"✨ {full_summary}")
                                progress_log.append(f"✨ {full_summary}")
                        except Exception as e:
                            logger.warning(f"Failed to generate completion summary: {e}")
                            # Enhanced fallback based on actual actions
                            tools_used = [t["tool"] for t in tool_results]
                            if "write_file" in tools_used and "replace_in_file" in tools_used:
                                log_progress("Perfect! Ik heb nieuwe bestanden aangemaakt én bestaande code aangepast. Check je applicatie - alle wijzigingen zijn live zichtbaar!", "✨")
                            elif "replace_in_file" in tools_used:
                                files_modified = len([t for t in tools_used if t == "replace_in_file"])
                                log_progress(f"Klaar! Code aangepast in {files_modified} bestand(en). Hot-reload toont alle wijzigingen direct in je app!", "✨")
                            elif "write_file" in tools_used:
                                files_created = len([t for t in tools_used if t == "write_file"])
                                log_progress(f"Succes! {files_created} nieuwe bestand(en) aangemaakt. Je applicatie heeft nu de gevraagde functionaliteit!", "✨")
                            elif "read_file" in tools_used:
                                log_progress("Analyse voltooid! Ik heb alle relevante bestanden bestudeerd en kan nu je vraag volledig beantwoorden!", "✨")
                            else:
                                log_progress(f"Plan uitgevoerd! Alle {len(tool_results)} stappen zijn succesvol voltooid!", "✨")
                    else:
                        log_progress("Ik ga je vraag direct beantwoorden zonder extra tools te gebruiken...", "✨")
                    
                    logger.info(f"Final response after {len(tool_results)} tool calls")
                    break
            
            # Store in memory
            self.memory.add(text=message, kind="user")
            self.memory.add(text=response, kind="assistant")
            
            # Note: No longer adding "Mijn proces" summary section
            # Progress updates are already sent in real-time via send_progress()
            # The final response should be clean and conversational like VS Code Copilot
            
            logger.info(f"Response: {response[:50]}...")
            return {"answer": response}
            
        except Exception as e:
            logger.error(f"Chat error: {e}", exc_info=True)
            return {"answer": f"Error: {str(e)}"}
        finally:
            # Always stop heartbeat when request completes
            heartbeat.stop()
    
    def list_models(self, params: dict) -> dict:
        """List available models"""
        try:
            models = self.llm.list_models()
            return {"models": models}
        except Exception as e:
            logger.error(f"List models error: {e}")
            return {"models": []}


class JSONRPCServer:
    """JSON-RPC 2.0 server"""
    
    def __init__(self):
        self.backend = OmniBackend()
        # Initialize tools and LLM after backend is created
        self.backend._init_tools_and_llm()
        self.methods = {
            "chat": self.backend.chat_streaming,  # Use streaming by default
            "chat_legacy": self.backend.chat,  # Keep old version for fallback
            "list_models": self.backend.list_models,
        }
    
    def handle_request(self, request: dict) -> dict:
        """Handle JSON-RPC request (with async support)"""
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})
        
        if not method or method not in self.methods:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": f"Unknown method: {method}"
            }
        
        try:
            # Get the method
            method_func = self.methods[method]
            
            # Check if it's async and run with asyncio if needed
            import inspect
            if inspect.iscoroutinefunction(method_func):
                result = asyncio.run(method_func(params))
            else:
                result = method_func(params)
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        except Exception as e:
            logger.error(f"Method {method} failed: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": str(e)
            }
    
    def run(self):
        """Main loop"""
        logger.info("JSON-RPC server started...")
        
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    response = self.handle_request(request)
                    print(json.dumps(response), flush=True)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error(f"Server error: {e}")


def main():
    logger.info("=" * 60)
    logger.info("Omni Electron Backend Starting")
    logger.info("=" * 60)
    
    server = JSONRPCServer()
    server.run()


if __name__ == "__main__":
    main()
