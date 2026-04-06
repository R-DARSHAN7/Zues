import httpx
from groq import AsyncGroq
from backend.core.config import settings

class LLMClient:
    def __init__(self):
        # Initialize Groq if we aren't using local Ollama
        if not settings.use_ollama:
            self._groq = AsyncGroq(api_key=settings.groq_api_key)

    async def generate_response(
        self, system_prompt: str, messages: list[dict]
    ) -> str:
        if settings.use_ollama:
            return await self._ollama(system_prompt, messages)
        return await self._groq_call(system_prompt, messages)

    async def _groq_call(
        self, system_prompt: str, messages: list[dict]
    ) -> str:
        try:
            resp = await self._groq.chat.completions.create(
                model="llama-3.1-8b-instant",  # Groq's high-speed 8B model
                messages=[
                    {"role": "system", "content": system_prompt}
                ] + messages,
                temperature=0.7,
                max_tokens=350,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"Groq error: {str(e)}"

    async def _ollama(
        self, system_prompt: str, messages: list[dict]
    ) -> str:
        payload = {
            "model": settings.ollama_model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "stream": False,
            "options": {
                "num_predict": 350,
                "temperature": 0.7,
                "num_ctx": 2048,
            }
        }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{settings.ollama_url}/api/chat", json=payload
                )
                resp.raise_for_status()
                return resp.json()["message"]["content"].strip()
        except Exception as e:
            return f"Ollama error: {str(e)}"