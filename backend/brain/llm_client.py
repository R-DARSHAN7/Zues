import httpx
from openai import AsyncOpenAI
from backend.core.config import settings

class LLMClient:
    def __init__(self):
        if not settings.use_ollama:
            self._openai = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_response(self, system_prompt: str, messages: list[dict]) -> str:
        if settings.use_ollama:
            return await self._ollama(system_prompt, messages)
        return await self._openai_call(system_prompt, messages)

    async def _openai_call(self, system_prompt: str, messages: list[dict]) -> str:
        try:
            resp = await self._openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system_prompt}] + messages,
                temperature=0.7, max_tokens=150,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"OpenAI error: {str(e)}"

    async def _ollama(self, system_prompt: str, messages: list[dict]) -> str:
        payload = {
            "model": settings.ollama_model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "stream": False,
            "options": {
                "num_predict": 350,  # Increased from 100 to allow long answers
                "temperature": 0.7,  # Increased slightly for better vocabulary/detail
                "num_ctx": 2048,    
            }
        }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(f"{settings.ollama_url}/api/chat", json=payload)
                resp.raise_for_status()
                return resp.json()["message"]["content"].strip()
        except Exception as e:
            return f"Ollama error: {str(e)}"
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(f"{settings.ollama_url}/api/chat", json=payload)
                resp.raise_for_status()
                return resp.json()["message"]["content"].strip()
        except Exception as e:
            return f"Ollama error: {str(e)}"