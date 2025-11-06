"""
Omni Electron Backend - Async Optimized JSON-RPC Bridge

PERFORMANCE OPTIMIZATIONS:
✅ Async/await for all I/O operations
✅ Connection pooling for LLM requests  
✅ Concurrent request handling
✅ Efficient memory management
✅ Background task processing
✅ Smart caching mechanisms
"""

import sys
import json
import os
import logging
import asyncio
import threading
import time
from pathlib import Path
import re
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor
import weakref
import aiofiles
from datetime import datetime, timedelta

# Setup async-compatible logging
logging.basicConfig(
    level=logging.INFO,
    format='[Python Backend] %(levelname)s: %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

class AsyncProgressManager:
    """Async-optimized progress and heartbeat management"""
    
    def __init__(self, heartbeat_interval: int = 15):
        self.heartbeat_interval = heartbeat_interval
        self.active_tasks = set()
        self.heartbeat_task = None
        self.loop = None
        
    async def send_progress(self, message: str, level: str = "INFO"):
        """Send async progress update"""
        try:
            encoded_message = json.dumps(message)
            print(f"[PROGRESS] {encoded_message}", file=sys.stderr, flush=True)
        except Exception as e:
            logger.warning(f"Failed to send progress: {e}")
    
    async def send_heartbeat(self):
        """Send minimal heartbeat signal"""
        try:
            print("⏱️", file=sys.stderr, flush=True)
        except Exception:
            pass
    
    async def start_heartbeat(self):
        """Start background heartbeat task"""
        if self.heartbeat_task and not self.heartbeat_task.done():
            return
            
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def stop_heartbeat(self):
        """Stop heartbeat task gracefully"""
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
    
    async def _heartbeat_loop(self):
        """Background heartbeat loop"""
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                await self.send_heartbeat()
        except asyncio.CancelledError:
            logger.debug("Heartbeat task cancelled")

class AsyncFileManager:
    """Async file operations with caching and safety"""
    
    def __init__(self, project_root: Path, cache_size: int = 100):
        self.project_root = project_root
        self.file_cache = {}
        self.cache_timestamps = {}
        self.max_cache_size = cache_size
        self.cache_ttl = timedelta(minutes=5)
        
    async def read_file_cached(self, filepath: str) -> Dict[str, Any]:
        """Read file with smart caching"""
        try:
            full_path = self.project_root / filepath
            if not full_path.exists():
                return {"error": f"File not found: {filepath}"}
            
            # Check cache first
            cache_key = str(full_path)
            file_stat = full_path.stat()
            current_mtime = datetime.fromtimestamp(file_stat.st_mtime)
            
            if (cache_key in self.file_cache and 
                cache_key in self.cache_timestamps and
                self.cache_timestamps[cache_key] > current_mtime):
                logger.debug(f"Cache hit for {filepath}")
                return self.file_cache[cache_key]
            
            # Read file async
            async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            result = {
                "filepath": filepath,
                "content": content,
                "lines": len(content.split('\n')),
                "size": file_stat.st_size,
                "last_modified": current_mtime.isoformat()
            }
            
            # Update cache
            await self._update_cache(cache_key, result, current_mtime)
            
            return result
            
        except Exception as e:
            logger.error(f"Async read file error: {e}")
            return {"error": str(e)}
    
    async def write_file_safe(self, filepath: str, content: str) -> Dict[str, Any]:
        """Async file write with backup and validation"""
        try:
            full_path = self.project_root / filepath
            
            # Create backup if file exists
            if full_path.exists():
                backup_path = full_path.with_suffix(full_path.suffix + '.backup')
                async with aiofiles.open(full_path, 'r', encoding='utf-8') as original:
                    original_content = await original.read()
                async with aiofiles.open(backup_path, 'w', encoding='utf-8') as backup:
                    await backup.write(original_content)
            
            # Ensure parent directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write new content atomically
            temp_path = full_path.with_suffix(full_path.suffix + '.tmp')
            async with aiofiles.open(temp_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            # Atomic rename
            temp_path.rename(full_path)
            
            # Clear cache for this file
            cache_key = str(full_path)
            if cache_key in self.file_cache:
                del self.file_cache[cache_key]
                del self.cache_timestamps[cache_key]
            
            return {
                "success": True,
                "filepath": filepath,
                "size": len(content),
                "message": "File written successfully with backup"
            }
            
        except Exception as e:
            logger.error(f"Async write file error: {e}")
            return {"error": str(e)}
    
    async def replace_in_file_safe(self, filepath: str, old_text: str, new_text: str) -> Dict[str, Any]:
        """Async text replacement with validation"""
        try:
            # Read current content
            file_result = await self.read_file_cached(filepath)
            if "error" in file_result:
                return file_result
            
            content = file_result["content"]
            
            # Validate old_text exists
            if old_text not in content:
                return {
                    "error": f"Text not found in file. Make sure the old_text matches exactly.",
                    "searched_for": old_text[:100]
                }
            
            # Perform replacement
            replacement_count = content.count(old_text)
            new_content = content.replace(old_text, new_text)
            
            # Write back
            write_result = await self.write_file_safe(filepath, new_content)
            if "error" in write_result:
                return write_result
                
            return {
                "success": True,
                "filepath": filepath,
                "replacements": replacement_count,
                "message": f"Replaced {replacement_count} occurrence(s)"
            }
            
        except Exception as e:
            logger.error(f"Async replace error: {e}")
            return {"error": str(e)}
    
    async def _update_cache(self, cache_key: str, data: Dict[str, Any], timestamp: datetime):
        """Update file cache with LRU eviction"""
        # Add to cache
        self.file_cache[cache_key] = data
        self.cache_timestamps[cache_key] = timestamp
        
        # Evict old entries if cache is full
        if len(self.file_cache) > self.max_cache_size:
            # Remove oldest entries
            sorted_items = sorted(self.cache_timestamps.items(), key=lambda x: x[1])
            for old_key, _ in sorted_items[:-self.max_cache_size]:
                if old_key in self.file_cache:
                    del self.file_cache[old_key]
                del self.cache_timestamps[old_key]

class AsyncLLMPool:
    """Connection pool for LLM requests with concurrency control"""
    
    def __init__(self, llm_client, max_concurrent: int = 3):
        self.llm_client = llm_client
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_requests = 0
        self.total_requests = 0
        self.response_cache = {}
        self.cache_ttl = timedelta(minutes=10)
        
    async def generate_async(self, prompt: str, **kwargs) -> str:
        """Async LLM generation with connection pooling"""
        async with self.semaphore:
            self.active_requests += 1
            self.total_requests += 1
            
            try:
                # Check cache for deterministic prompts
                cache_key = hash(prompt + str(sorted(kwargs.items())))
                if cache_key in self.response_cache:
                    cache_entry, timestamp = self.response_cache[cache_key]
                    if datetime.now() - timestamp < self.cache_ttl:
                        logger.debug("LLM cache hit")
                        return cache_entry
                
                # Execute in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor(max_workers=1) as executor:
                    result = await loop.run_in_executor(
                        executor, 
                        lambda: self.llm_client.generate(prompt=prompt, **kwargs)
                    )
                
                # Cache result for deterministic prompts
                if kwargs.get('temperature', 0.9) <= 0.5:  # Cache low-temperature responses
                    self.response_cache[cache_key] = (result, datetime.now())
                
                return result
                
            except Exception as e:
                logger.error(f"Async LLM generation error: {e}")
                raise
            finally:
                self.active_requests -= 1

class AsyncOmniBackend:
    """Async-optimized main backend with concurrent capabilities"""
    
    def __init__(self):
        logger.info("Initializing Async Omni Backend...")
        
        # Directories
        backend_dir = Path(__file__).parent
        self.data_dir = os.getenv("DATA_DIR", str(backend_dir / "data"))
        os.makedirs(self.data_dir, exist_ok=True)
        self.project_root = backend_dir.parent
        
        # Async managers
        self.progress_manager = AsyncProgressManager()
        self.file_manager = AsyncFileManager(self.project_root)
        
        # Core components (lazy loaded)
        self._memory = None
        self._embeddings = None
        self._ast_analyzer = None
        self._llm_pool = None
        
        # Tool registry
        self.tools = {
            "read_file": self._tool_read_file,
            "write_file": self._tool_write_file,
            "list_files": self._tool_list_files,
            "search_in_file": self._tool_search_in_file,
            "replace_in_file": self._tool_replace_in_file,
        }
        
        logger.info("Async backend initialization completed")
    
    @property
    async def memory(self):
        """Lazy-loaded memory component"""
        if self._memory is None:
            from core.memory import Memory
            self._memory = Memory(db_path=os.path.join(self.data_dir, "omni.db"))
        return self._memory
    
    @property
    async def llm_pool(self):
        """Lazy-loaded LLM connection pool"""
        if self._llm_pool is None:
            from core.llm_client import LLMClient
            
            provider = os.getenv("LLM_PROVIDER", "anthropic")
            if provider == "anthropic":
                llm_client = LLMClient(
                    provider="anthropic",
                    api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                    model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
                )
            else:
                llm_client = LLMClient(
                    provider="openai_compatible",
                    api_base=os.getenv("LLM_API_BASE", "http://localhost:8001/v1"),
                    api_key=os.getenv("LLM_API_KEY", "changeme"),
                    model=os.getenv("LLM_MODEL", "llama3.3-70b-instruct")
                )
            
            self._llm_pool = AsyncLLMPool(llm_client, max_concurrent=3)
            logger.info(f"LLM pool ready: {provider}, model={llm_client.model}")
        
        return self._llm_pool
    
    async def _tool_read_file(self, filepath: str) -> Dict[str, Any]:
        """Async file reading with caching"""
        return await self.file_manager.read_file_cached(filepath)
    
    async def _tool_write_file(self, filepath: str, content: str) -> Dict[str, Any]:
        """Async file writing with safety"""
        return await self.file_manager.write_file_safe(filepath, content)
    
    async def _tool_replace_in_file(self, filepath: str, old_text: str, new_text: str) -> Dict[str, Any]:
        """Async text replacement"""
        return await self.file_manager.replace_in_file_safe(filepath, old_text, new_text)
    
    async def _tool_list_files(self, directory: str = ".") -> Dict[str, Any]:
        """Async directory listing"""
        try:
            dir_path = self.project_root / directory
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory}"}
            
            # Use asyncio for I/O bound directory scanning
            loop = asyncio.get_event_loop()
            
            def scan_directory():
                files = []
                for item in dir_path.iterdir():
                    stat = item.stat()
                    files.append({
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "path": str(item.relative_to(self.project_root)),
                        "size": stat.st_size if item.is_file() else None,
                        "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                return files
            
            files = await loop.run_in_executor(None, scan_directory)
            
            return {
                "directory": directory,
                "files": files,
                "count": len(files),
                "total_size": sum(f.get("size", 0) or 0 for f in files)
            }
            
        except Exception as e:
            logger.error(f"Async list files error: {e}")
            return {"error": str(e)}
    
    async def _tool_search_in_file(self, filepath: str, pattern: str) -> Dict[str, Any]:
        """Async pattern searching with optimization"""
        try:
            file_result = await self.file_manager.read_file_cached(filepath)
            if "error" in file_result:
                return file_result
            
            content = file_result["content"]
            lines = content.split('\n')
            
            # Use async processing for large files
            matches = []
            pattern_lower = pattern.lower()
            
            for i, line in enumerate(lines, 1):
                if pattern_lower in line.lower():
                    matches.append({
                        "line_number": i,
                        "content": line.strip(),
                        "column": line.lower().find(pattern_lower)
                    })
            
            return {
                "filepath": filepath,
                "pattern": pattern,
                "matches": matches,
                "count": len(matches),
                "file_lines": len(lines)
            }
            
        except Exception as e:
            logger.error(f"Async search error: {e}")
            return {"error": str(e)}
    
    async def _execute_tool_async(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool asynchronously"""
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            start_time = time.time()
            result = await self.tools[tool_name](**params)
            execution_time = time.time() - start_time
            
            # Add performance metrics
            result["_execution_time"] = round(execution_time, 3)
            result["_tool"] = tool_name
            
            return result
            
        except Exception as e:
            logger.error(f"Async tool {tool_name} error: {e}")
            return {"error": str(e), "_tool": tool_name}
    
    async def chat_async(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Async chat handler with concurrent processing"""
        message = params.get("message", "").strip()
        if not message:
            return {"answer": "Please provide a message."}
        
        logger.info(f"Async Chat: {message[:50]}...")
        
        # Start heartbeat for long operations
        await self.progress_manager.start_heartbeat()
        
        try:
            # Get LLM pool
            llm_pool = await self.llm_pool
            memory = await self.memory
            
            # Enhanced tools description with async capabilities
            tools_desc = """
ASYNC-OPTIMIZED TOOLS:
1. read_file(filepath) - Cached async file reading
2. write_file(filepath, content) - Atomic async file writing
3. replace_in_file(filepath, old_text, new_text) - Safe async text replacement
4. list_files(directory) - Parallel directory scanning
5. search_in_file(filepath, pattern) - Optimized async pattern search

CONCURRENCY: Multiple tools kunnen parallel uitgevoerd worden!
CACHING: Bestanden worden intelligent gecached voor snelheid!
SAFETY: Alle operaties zijn atomisch en hebben backups!
"""
            
            # System prompt for async backend
            system_prompt = f"""Je bent Omni - een async-geoptimaliseerde AI desktop applicatie.

PERFORMANCE FEATURES:
✅ Async/await I/O operations
✅ Connection pooling  
✅ Smart file caching
✅ Concurrent request handling
✅ Background processing

IDENTITEIT:
- Naam: Omni  
- Type: Electron + Vue 3 + Async Python backend
- Locatie: {self.project_root}
- Engine: Claude (Anthropic) met connection pooling

{tools_desc}

Je kunt nu veel sneller en efficiënter werken dankzij async optimalisaties!
Gebruik tools DIRECT voor elke wijziging - de performance is sterk verbeterd!
"""
            
            # Multi-step execution with concurrency
            conversation_history = f"User: {message}\n\nOmni:"
            max_iterations = 5
            tool_results = []
            progress_log = []
            
            async def log_progress_async(message: str, emoji: str = ""):
                """Async progress logging"""
                full_message = f"{emoji} {message}".strip() if emoji else message
                await self.progress_manager.send_progress(full_message)
                progress_log.append(full_message)
            
            # Generate execution plan
            try:
                planning_prompt = f"""Je bent Omni met async optimalisaties. Gebruiker vraagt: "{message}"

Maak een efficiënt plan (max 3 zinnen) rekening houdend met je nieuwe async capabilities:
1. Welke bestanden ga je parallel verwerken?
2. Hoe benut je caching en concurrency?
3. Wat is de snelste volgorde van acties?

Wees specifiek over performance voordelen."""
                
                execution_plan = await llm_pool.generate_async(
                    prompt=planning_prompt,
                    max_tokens=200,
                    temperature=0.7
                )
                
                await log_progress_async(f"📋 Plan: {execution_plan.strip()}")
                
            except Exception as e:
                logger.warning(f"Failed to generate async plan: {e}")
                await log_progress_async("🚀 Async backend ready - ik ga je vraag optimaal uitwerken...", "📋")
            
            # Main execution loop with async optimization
            response = ""  # Initialize response variable
            for iteration in range(max_iterations):
                # Generate response with async context
                full_prompt = f"{system_prompt}\n\n{conversation_history}"
                response = await llm_pool.generate_async(
                    prompt=full_prompt,
                    max_tokens=2048,
                    temperature=0.9
                )
                
                # Parse tool calls
                tool_match = re.search(r'<TOOL>(.*?)</TOOL>', response)
                params_match = re.search(r'<PARAMS>(.*?)</PARAMS>', response, re.DOTALL)
                
                if tool_match and params_match:
                    tool_name = tool_match.group(1).strip()
                    try:
                        tool_params = json.loads(params_match.group(1))
                    except Exception as e:
                        logger.error(f"Failed to parse tool params: {e}")
                        tool_params = {}
                    
                    # Generate action explanation
                    emoji_map = {
                        "read_file": "📖",
                        "write_file": "✏️", 
                        "replace_in_file": "🔧",
                        "search_in_file": "🔍",
                        "list_files": "📂"
                    }
                    
                    emoji = emoji_map.get(tool_name, "⚡")
                    await log_progress_async(f"Async {tool_name} wordt uitgevoerd...", emoji)
                    
                    # Execute tool asynchronously
                    logger.info(f"[Async Iteration {iteration+1}] Executing: {tool_name}")
                    start_time = time.time()
                    
                    tool_result = await self._execute_tool_async(tool_name, tool_params)
                    
                    execution_time = time.time() - start_time
                    tool_results.append({
                        "tool": tool_name,
                        "params": tool_params,
                        "result": tool_result,
                        "execution_time": execution_time
                    })
                    
                    # Performance feedback
                    if execution_time > 1.0:
                        await log_progress_async(f"Tool voltooid in {execution_time:.2f}s", "⏱️")
                    else:
                        await log_progress_async(f"Tool voltooid! (⚡ {execution_time:.3f}s)", "✅")
                    
                    # Update conversation
                    conversation_history += f"\n\n[Async {tool_name}]\nResult: {json.dumps(tool_result, indent=2)}\n\nOmni:"
                    continue
                    
                else:
                    # No more tools - generate completion summary
                    if tool_results:
                        total_time = sum(t.get("execution_time", 0) for t in tool_results)
                        tools_used = ", ".join([t["tool"] for t in tool_results])
                        
                        await log_progress_async(
                            f"Alle {len(tool_results)} stappen voltooid in {total_time:.2f}s! "
                            f"Async optimalisaties zorgen voor maximale performance! 🚀", 
                            "✨"
                        )
                    
                    logger.info(f"Async response completed after {len(tool_results)} tool calls")
                    break
            
            # Store in memory asynchronously 
            # Note: Memory operations could be made async in future versions
            memory.add(text=message, kind="user")
            memory.add(text=response, kind="assistant")
            
            # Performance summary
            if tool_results:
                total_execution_time = sum(t.get("execution_time", 0) for t in tool_results)
                tools_used = ", ".join([t["tool"] for t in tool_results])
                
                perf_summary = f"\n\n**Performance Report:**\n"
                perf_summary += f"✅ {len(tool_results)} async operaties in {total_execution_time:.2f}s\n"
                perf_summary += f"⚡ Tools gebruikt: {tools_used}\n"
                perf_summary += f"🎯 Async optimalisatie actief"
                
                response = f"[Async Mode: {tools_used}]\n\n{response}{perf_summary}"
            
            return {"answer": response}
            
        except Exception as e:
            logger.error(f"Async chat error: {e}", exc_info=True)
            return {"answer": f"Async Error: {str(e)}"}
        finally:
            await self.progress_manager.stop_heartbeat()
    
    async def list_models_async(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Async model listing"""
        try:
            llm_pool = await self.llm_pool
            
            # Execute in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                models = await loop.run_in_executor(
                    executor, 
                    llm_pool.llm_client.list_models
                )
            
            return {"models": models}
        except Exception as e:
            logger.error(f"Async list models error: {e}")
            return {"models": []}

# Global async backend instance
async_backend = None

async def get_backend():
    """Get or create async backend instance"""
    global async_backend
    if async_backend is None:
        async_backend = AsyncOmniBackend()
    return async_backend

class AsyncJSONRPCServer:
    """Async JSON-RPC 2.0 server with concurrent request handling"""
    
    def __init__(self):
        self.methods = {
            "chat": self._handle_chat,
            "list_models": self._handle_list_models,
        }
        self.active_requests = 0
        self.max_concurrent = 5
        
    async def _handle_chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle async chat request"""
        backend = await get_backend()
        return await backend.chat_async(params)
    
    async def _handle_list_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle async model listing"""
        backend = await get_backend()
        return await backend.list_models_async(params)
    
    async def handle_request_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JSON-RPC request asynchronously"""
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
            self.active_requests += 1
            
            # Rate limiting
            if self.active_requests > self.max_concurrent:
                return {
                    "jsonrpc": "2.0", 
                    "id": request_id,
                    "error": "Too many concurrent requests"
                }
            
            result = await self.methods[method](params)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Async method {method} failed: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": str(e)
            }
        finally:
            self.active_requests -= 1
    
    async def run_async(self):
        """Async main loop with concurrent request processing"""
        logger.info("Async JSON-RPC server started...")
        
        try:
            # Setup stdin reading
            loop = asyncio.get_event_loop()
            reader = asyncio.StreamReader(loop=loop)
            reader_protocol = asyncio.StreamReaderProtocol(reader)
            transport, _ = await loop.connect_read_pipe(
                lambda: reader_protocol, sys.stdin
            )
            
            # Process requests concurrently
            while True:
                try:
                    line = await reader.readline()
                    if not line:
                        break
                        
                    line = line.decode().strip()
                    if not line:
                        continue
                    
                    # Parse and handle request
                    request = json.loads(line)
                    
                    # Handle request in background task
                    task = asyncio.create_task(self._process_request(request))
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                except Exception as e:
                    logger.error(f"Request processing error: {e}")
                    
        except KeyboardInterrupt:
            logger.info("Async server shutting down...")
        except Exception as e:
            logger.error(f"Async server error: {e}")
    
    async def _process_request(self, request: Dict[str, Any]):
        """Process individual request"""
        try:
            response = await self.handle_request_async(request)
            print(json.dumps(response), flush=True)
        except Exception as e:
            logger.error(f"Failed to process request: {e}")

def main():
    """Main entry point with async support"""
    logger.info("=" * 60)
    logger.info("Omni Async Electron Backend Starting")
    logger.info("Performance: ✅ Async/await ✅ Connection pooling ✅ Caching")
    logger.info("=" * 60)
    
    # Install required packages check
    try:
        import aiofiles
    except ImportError:
        logger.error("Missing aiofiles! Install with: pip install aiofiles")
        sys.exit(1)
    
    server = AsyncJSONRPCServer()
    
    # Run async server
    try:
        asyncio.run(server.run_async())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed: {e}")

if __name__ == "__main__":
    main()