from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import transmitters
from .audio import AudioPipeline
from .config import Settings
from .streaming import BroadcastHub, ListenerLimitReached

load_dotenv()
settings = Settings.from_env()
raw_hub = BroadcastHub(settings.max_listeners)
clean_hub = BroadcastHub(settings.max_listeners)
pipeline = AudioPipeline(settings, raw_hub, clean_hub)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    loop = asyncio.get_running_loop()
    raw_hub.attach_loop(loop)
    clean_hub.attach_loop(loop)
    pipeline.start()
    try:
        yield
    finally:
        pipeline.stop()


app = FastAPI(
    title="VLF Noise Scout",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/api/status")
async def status() -> dict:
    return pipeline.status()


@app.get("/api/transmitters")
async def transmitter_scan() -> dict:
    return transmitters.load()


@app.get("/stream/{kind}.mp3")
async def stream(kind: str) -> StreamingResponse:
    hub = clean_hub if kind == "clean" else raw_hub if kind == "raw" else None
    if hub is None:
        raise HTTPException(status_code=404, detail="stream not found")
    try:
        client = hub.subscribe()
    except ListenerLimitReached as exc:
        raise HTTPException(status_code=503, detail="listener limit reached") from exc
    generator = hub.stream(client)
    return StreamingResponse(
        generator,
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Content-Type-Options": "nosniff",
        },
    )


web_root = Path(__file__).resolve().parents[2] / "web"
if web_root.exists():
    app.mount("/", StaticFiles(directory=web_root, html=True), name="web")
