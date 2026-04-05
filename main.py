import os
import json
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from backend.core.config import settings
from backend.core.database import init_db, AsyncSessionLocal
from backend.core.history import save_turn, get_recent
from backend.brain.llm_client import LLMClient
from backend.brain.router import IntentRouter
from backend.domains.education import EducationDomain
from backend.domains.home_control import HomeControlDomain
from backend.audio.tts import TTSEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zeus")

AUDIO_DIR = os.path.join("static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)


def cleanup_audio():
    cutoff = datetime.now(timezone.utc) - timedelta(
        minutes=settings.audio_ttl_minutes
    )
    deleted = 0
    for filename in os.listdir(AUDIO_DIR):
        filepath = os.path.join(AUDIO_DIR, filename)
        try:
            mtime = datetime.fromtimestamp(
                os.path.getmtime(filepath), tz=timezone.utc
            )
            if mtime < cutoff:
                os.remove(filepath)
                deleted += 1
        except OSError:
            pass
    if deleted:
        logger.info(f"Audio cleanup: removed {deleted} file(s).")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("ZEUS online. Supabase connected.")

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        cleanup_audio,
        trigger="interval",
        minutes=settings.audio_ttl_minutes,
        id="audio_cleanup",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        f"Audio cleanup scheduled every {settings.audio_ttl_minutes} min."
    )

    yield

    scheduler.shutdown(wait=False)
    logger.info("ZEUS shutting down.")


app = FastAPI(title="ZEUS v2", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/audio",  StaticFiles(directory="static/audio"), name="audio")

llm       = LLMClient()
router    = IntentRouter(llm)
education = EducationDomain(llm)
home      = HomeControlDomain(llm)
tts       = TTSEngine()


@app.get("/")
def root():
    with open("static/index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    profile_id = "default"
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            text       = data.get("text", "").strip()
            profile_id = data.get("profile_id", "default")

            if not text:
                continue

            logger.info(f"[{profile_id}] User: {text}")

            async with AsyncSessionLocal() as db:
                history = await get_recent(db, profile_id, limit=8)

            messages = history + [{"role": "user", "content": text}]
            intent   = await router.classify(text)

            if intent == "home":
                bot_text = await home.process(messages, profile_id)
            else:
                bot_text = await education.process(messages, profile_id)

            logger.info(f"[{profile_id}] ZEUS [{intent}]: {bot_text}")

            audio_url, _ = await asyncio.gather(
                tts.generate(bot_text),
                _persist(profile_id, text, bot_text, intent),
            )

            await websocket.send_json({
                "response":  bot_text,
                "intent":    intent,
                "audio_url": audio_url,
            })

    except WebSocketDisconnect:
        logger.info(f"Client disconnected — profile: {profile_id}")


async def _persist(
    profile_id: str, user_text: str, bot_text: str, domain: str
):
    async with AsyncSessionLocal() as db:
        await save_turn(db, profile_id, user_text, bot_text, domain)