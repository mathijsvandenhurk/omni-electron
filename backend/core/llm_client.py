import os
import requests
from typing import List, Optional

class LLMClient:
    """
    Minimal client for OpenAI-compatible endpoints and Anthropic API.
    Supports both vLLM/TGI/llama.cpp (OpenAI-compatible) and Anthropic Claude.
    """
    def __init__(self, provider: str = "openai_compatible", api_base: str = "http://localhost:8001/v1", api_key: str = "", model: str = "local-model"):
        self.provider = provider
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.model = model
        self.session = requests.Session()
        
        # Anthropic-specific config
        if provider == "anthropic":
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
            self.api_base = "https://api.anthropic.com"
            self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    def _headers(self):
        if self.provider == "anthropic":
            return {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
        else:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            return headers

    def list_models(self):
        url = f"{self.api_base}/models"
        resp = self.session.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # Expect OpenAI-like {data:[{id:...,object:'model',...}]}
        if isinstance(data, dict) and "data" in data:
            return [m.get("id") for m in data.get("data", []) if isinstance(m, dict) and m.get("id")]
        # Fallback generic
        if isinstance(data, list):
            return data
        return []

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.2, model: str | None = None, timeout: int = 60) -> str:
        headers = self._headers()
        
        if self.provider == "anthropic":
            # Anthropic API format
            url = f"{self.api_base}/v1/messages"
            # Use provided model only if it looks like an Anthropic model, otherwise use self.model
            use_model = model if (model and model.startswith("claude")) else self.model
            payload = {
                "model": use_model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            resp = self.session.post(url, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            # Anthropic response structure
            try:
                if "content" in data and isinstance(data["content"], list) and len(data["content"]) > 0:
                    return data["content"][0].get("text", "").strip()
                return ""
            except Exception:
                return str(data)
        else:
            # OpenAI-compatible format
            url = f"{self.api_base}/chat/completions"
            payload = {
                "model": model or self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False
            }
            resp = self.session.post(url, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            # OpenAI-compatible structure
            try:
                message = data["choices"][0]["message"]
                # Some models (like reasoning models) may have reasoning_content and content=None
                # Try content first, then reasoning_content, then fallback
                content = message.get("content")
                if content is None or content == "":
                    # Try reasoning_content for reasoning models
                    content = message.get("reasoning_content")
                if content:
                    return content.strip()
                return ""
            except Exception:
                # Fallbacks for partially compatible servers
                if isinstance(data, dict) and "text" in data:
                    return str(data["text"]).strip()
                return str(data)

    def generate_with_tools(self, messages: list[dict], tools: list[dict], max_tokens: int = 4096, temperature: float = 0.2, model: str | None = None, timeout: int = 120) -> dict:
        """
        Generate with tool calling support (Anthropic format).
        Returns dict with 'stop_reason', 'content' (list of content blocks), and 'usage'.
        Content blocks can be type 'text' or 'tool_use'.
        """
        headers = self._headers()
        
        if self.provider == "anthropic":
            url = f"{self.api_base}/v1/messages"
            use_model = model if (model and model.startswith("claude")) else self.model
            payload = {
                "model": use_model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
                "tools": tools
            }
            resp = self.session.post(url, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        else:
            # OpenAI-compatible format (convert from Anthropic to OpenAI format)
            url = f"{self.api_base}/chat/completions"
            
            # Convert Anthropic messages to OpenAI format
            openai_messages = []
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                
                # Handle different content formats
                if isinstance(content, str):
                    openai_messages.append({"role": role, "content": content})
                elif isinstance(content, list):
                    # Flatten content blocks to text for OpenAI
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict):
                            if block.get("type") == "text":
                                text_parts.append(block.get("text", ""))
                            elif block.get("type") == "tool_result":
                                text_parts.append(f"Tool result: {block.get('content', '')}")
                        else:
                            text_parts.append(str(block))
                    openai_messages.append({"role": role, "content": "\n".join(text_parts)})
            
            # Convert Anthropic tools to OpenAI format
            openai_tools = []
            for tool in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("input_schema", {})
                    }
                })
            
            payload = {
                "model": model or self.model,
                "messages": openai_messages,
                "tools": openai_tools,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            resp = self.session.post(url, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            
            # Convert OpenAI response to Anthropic format
            choice = data["choices"][0]
            message = choice["message"]
            
            content = []
            if message.get("content"):
                content.append({"type": "text", "text": message["content"]})
            
            if message.get("tool_calls"):
                for tc in message["tool_calls"]:
                    content.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["function"]["name"],
                        "input": tc["function"]["arguments"]
                    })
            
            return {
                "stop_reason": "tool_use" if message.get("tool_calls") else "end_turn",
                "content": content,
                "usage": data.get("usage", {})
            }
