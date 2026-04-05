import os
import uuid
import httpx
import edge_tts
from backend.core.config import settings

AUDIO_DIR = os.path.join("static", "audio")


class TTSEngine:
    async def generate(self, text: str) -> str:
        os.makedirs(AUDIO_DIR, exist_ok=True)
        filename = f"zeus_{uuid.uuid4().hex[:10]}"

        if settings.elevenlabs_api_key:
            url = (
                f"https://api.elevenlabs.io/v1/text-to-speech/"
                f"{settings.elevenlabs_voice_id}"
            )
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": settings.elevenlabs_api_key,
            }
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5,
                },
            }
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        path = os.path.join(AUDIO_DIR, f"{filename}.mp3")
                        with open(path, "wb") as f:
                            f.write(resp.content)
                        return f"/audio/{filename}.mp3"
                    print(f"ElevenLabs error {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"ElevenLabs exception: {e}")

        # Fallback: Microsoft edge-tts (free, async, neural quality)
        path = os.path.join(AUDIO_DIR, f"{filename}.mp3")
        communicate = edge_tts.Communicate(text, voice="en-US-GuyNeural")
        await communicate.save(path)
        return f"/audio/{filename}.mp3"