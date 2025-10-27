# app/ai/llm.py
import os
import httpx
from typing import List, Dict, Optional

class OllamaClient:
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None, timeout: float = 30.0):
        self.base = (base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL") or "llama3.2:latest"
        self.client = httpx.AsyncClient(base_url=self.base, timeout=timeout)

    async def generate(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        """
        Uses Ollama native chat endpoint: POST /api/chat
        Payload shape:
          { "model": "...", "messages": [{"role":"system","content":"..."}, {"role":"user","content":"..."}], "stream": false }
        Response shape:
          { "message": {"role":"assistant","content":"..."}, ... }
        """
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)

        r = await self.client.post("/api/chat", json={
            "model": self.model,
            "messages": msgs,
            "stream": False
        })
        r.raise_for_status()
        data = r.json()
        return data.get("message", {}).get("content", "")

    async def aclose(self):
        await self.client.aclose()