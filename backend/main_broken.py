#!/usr/bin/env python3

import os
import sys
import json
import logging
import re
import time
import threading
from pathlib import Path
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.llm_client import LLMClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[Python Backend] %(levelname)s: %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Global variables for model configuration
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

def send_progress(message: str):
    """Send progress update to frontend via stderr"""
    print(f"[PROGRESS] {message}", file=sys.stderr, flush=True)

def send_heartbeat():
    """Send heartbeat to keep connection alive"""
    print("⏱️", file=sys.stderr, flush=True)

class HeartbeatManager:
    """Manages heartbeat signals for long-running operations"""
    def __init__(self):
        self.timer = None
        
    def start(self):
        """Start periodic heartbeat"""
        self.stop()  # Stop any existing timer
        self._send_heartbeat()
        
    def _send_heartbeat(self):
        """Send heartbeat and schedule next one"""
        send_heartbeat()
        self.timer = threading.Timer(30.0, self._send_heartbeat)
        self.timer.start()
        
    def stop(self):
        """Stop heartbeat"""
        if self.timer:
            self.timer.cancel()
            self.timer = None

# Global heartbeat manager
heartbeat = HeartbeatManager()

class OmniBackend:
    """Clean backend with VS Code style progress"""
    
    def __init__(self):
        """Initialize the backend"""
        # Set project root
        self.project_root = Path(__file__).parent.parent
        
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
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "filepath": filepath,
                "size": len(content),
                "success": True
            }
        except Exception as e:
            return {"error": str(e)}

    def _tool_list_files(self, directory: str = ".") -> dict:
        """List files in a directory"""
        try:
            full_path = self.project_root / directory
            if not full_path.exists():
                return {"error": f"Directory not found: {directory}"}
            
            files = []
            for item in full_path.iterdir():
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

    def _tool_search_in_file(self, filepath: str, search_text: str) -> dict:
        """Search for text in a file"""
        try:
            full_path = self.project_root / filepath
            if not full_path.exists():
                return {"error": f"File not found: {filepath}"}
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            matches = []
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if search_text in line:
                    matches.append({
                        "line": i,
                        "content": line.strip(),
                        "context": lines[max(0, i-2):i+1]
                    })
            
            return {
                "filepath": filepath,
                "search_text": search_text,
                "matches": matches,
                "count": len(matches)
            }
        except Exception as e:
            return {"error": str(e)}

    def _tool_replace_in_file(self, filepath: str, old_text: str, new_text: str) -> dict:
        """Replace text in a file"""
        try:
            full_path = self.project_root / filepath
            if not full_path.exists():
                return {"error": f"File not found: {filepath}"}
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if old_text not in content:
                return {"error": f"Text not found in file: {old_text}"}
            
            new_content = content.replace(old_text, new_text)
            replacements = content.count(old_text)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return {
                "filepath": filepath,
                "replacements": replacements,
                "success": True
            }
        except Exception as e:
            return {"error": str(e)}

    def chat(self, params: dict) -> dict:
        """Handle chat with VS Code style progress"""
        message = params.get("message", "").strip()
        if not message:
            return {"answer": "Please provide a message."}
        
        logger.info(f"Chat: {message[:50]}...")
        
        # Start heartbeat for long operations
        heartbeat.start()
        
        try:
            # VS Code style progress system
            send_progress("🤔 Analyzing request...")
            
            # System prompt
            system_prompt = f"""Je bent Omni, een intelligente assistant die direct actie onderneemt.

BESCHIKBARE TOOLS:
1. read_file(filepath) - Lees een bestand uit het project
2. write_file(filepath, content) - Schrijf content naar een bestand  
3. list_files(directory) - Toon bestanden in een directory
4. search_in_file(filepath, search_text) - Zoek tekst in een bestand
5. replace_in_file(filepath, old_text, new_text) - Vervang tekst in een bestand

GEBRUIK TOOLS FORMAT:
<TOOL>tool_name</TOOL>
<PARAMS>{{"param": "value"}}</PARAMS>

GEDRAGSREGELS:
- ACTIE EERST: Gebruik direct tools wanneer nodig
- Wees specifiek: noem exacte bestanden en wijzigingen
- Korte antwoorden: geen lange uitleg tenzij gevraagd
- Hot-reload werkt: wijzigingen zijn direct zichtbaar

Project root: {self.project_root}
"""
            
            # Multi-step execution
            conversation_history = f"User: {message}\n\nOmni:"
            max_iterations = 10
            tool_results = []
            response = ""
            
            # Create execution plan
            send_progress("📋 Creating execution plan...")
            planning_prompt = f"""Gebruiker vraagt: "{message}"

Maak een kort plan (max 3 zinnen):
1. Welke bestanden ga je bekijken?
2. Welke wijzigingen ga je maken?
3. In welke volgorde?"""
            
            try:
                send_heartbeat()
                plan = self.llm.generate(
                    prompt=planning_prompt,
                    max_tokens=150,
                    temperature=0.7
                )
                send_heartbeat()
                
                # Show plan summary
                plan_summary = plan.strip().split('\n')[0][:80] + "..."
                send_progress(f"📋 Plan: {plan_summary}")
                
            except Exception as e:
                logger.warning(f"Planning failed: {e}")
                send_progress("📋 Plan: Direct execution...")
            
            send_progress("🚀 Starting execution...")
            
            # Execute with tools
            for iteration in range(max_iterations):
                send_progress(f"💭 Thinking... (step {iteration + 1})")
                
                full_prompt = f"{system_prompt}\n\n{conversation_history}"
                send_heartbeat()
                
                response = self.llm.generate(
                    prompt=full_prompt,
                    max_tokens=2048,
                    temperature=0.9
                )
                send_heartbeat()
                
                # Check for tools
                tool_match = re.search(r'<TOOL>(.*?)</TOOL>', response)
                params_match = re.search(r'<PARAMS>(.*?)</PARAMS>', response, re.DOTALL)
                
                if tool_match and params_match:
                    tool_name = tool_match.group(1).strip()
                    try:
                        tool_params = json.loads(params_match.group(1))
                    except Exception as e:
                        logger.error(f"Failed to parse tool params: {e}")
                        continue
                    
                    # Show action
                    if tool_name == "read_file":
                        filepath = tool_params.get("filepath", "")
                        send_progress(f"📖 Reading: {filepath}")
                    elif tool_name == "write_file":
                        filepath = tool_params.get("filepath", "")
                        send_progress(f"📝 Creating: {filepath}")
                    elif tool_name == "replace_in_file":
                        filepath = tool_params.get("filepath", "")
                        send_progress(f"✏️ Modifying: {filepath}")
                    elif tool_name == "search_in_file":
                        filepath = tool_params.get("filepath", "")
                        send_progress(f"🔍 Searching: {filepath}")
                    elif tool_name == "list_files":
                        directory = tool_params.get("directory", ".")
                        send_progress(f"📂 Scanning: {directory}")
                    
                    # Execute tool
                    if tool_name in self.tools:
                        tool_result = self.tools[tool_name](**tool_params)
                        tool_results.append({
                            "tool": tool_name,
                            "params": tool_params,
                            "result": tool_result
                        })
                        
                        # Show result
                        if tool_result.get("success") or (tool_result.get("error") is None and tool_result.get("content")):
                            if tool_name == "read_file":
                                lines = tool_result.get("lines", 0)
                                send_progress(f"✅ Read {lines} lines")
                            elif tool_name == "write_file":
                                send_progress("✅ File created")
                            elif tool_name == "replace_in_file":
                                count = tool_result.get("replacements", 0)
                                send_progress(f"✅ {count} change(s) applied")
                            elif tool_name == "search_in_file":
                                count = tool_result.get("count", 0)
                                send_progress(f"✅ {count} match(es) found")
                            elif tool_name == "list_files":
                                count = tool_result.get("count", 0)
                                send_progress(f"✅ {count} items found")
                        else:
                            error = tool_result.get("error", "Unknown error")
                            send_progress(f"❌ Error: {error}")
                        
                        # Update conversation
                        conversation_history += f"\n\n{response}\n\nResult: {tool_result}"
                    else:
                        send_progress(f"❌ Unknown tool: {tool_name}")
                        break
                else:
                    # No more tools - done
                    send_progress("✨ Task completed!")
                    break
            
            # Clean response (remove tool calls)
            clean_response = re.sub(r'<TOOL>.*?</TOOL>', '', response)
            clean_response = re.sub(r'<PARAMS>.*?</PARAMS>', '', clean_response, flags=re.DOTALL)
            clean_response = clean_response.strip()
            
            logger.info(f"Response: {clean_response[:50]}...")
            return {"answer": clean_response}
            
        except Exception as e:
            logger.error(f"Chat error: {e}", exc_info=True)
            return {"answer": f"Error: {str(e)}"}
        finally:
            # Always stop heartbeat
            heartbeat.stop()

# JSON-RPC Server setup (same as before)
def handle_request(line: str) -> str:
    """Handle a single JSON-RPC request"""
    try:
        request = json.loads(line)
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        # Route requests
        if method == "chat":
            result = backend.chat(params)
        else:
            result = {"error": f"Unknown method: {method}"}
        
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        
        return json.dumps(response)
        
    except Exception as e:
        logger.error(f"Request handling error: {e}")
        error_response = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32603, "message": str(e)}
        }
        return json.dumps(error_response)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Omni Electron Backend Starting")
    logger.info("=" * 60)
    logger.info("Initializing Omni Backend...")
    
    # Initialize backend
    backend = OmniBackend()
    
    logger.info(f"Backend ready: anthropic, model={MODEL}")
    logger.info("JSON-RPC server started...")
    
    # Main server loop
    try:
        for line in sys.stdin:
            line = line.strip()
            if line:
                response = handle_request(line)
                print(response, flush=True)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        heartbeat.stop()