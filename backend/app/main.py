import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.postgres import init_db, close_db
from app.db.redis_client import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    print("✅ PostgreSQL connected")

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: OPENAI_API_KEY not set — agents will fail")
    else:
        print("✅ OpenAI API key found")

    print("🚀 AutoCrew backend ready")
    print("   API:    http://localhost:8000")
    print("   Docs:   http://localhost:8000/docs")

    yield

    await close_db()
    await close_redis()


app = FastAPI(title="AutoCrew API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import tasks, ws  # noqa: E402

app.include_router(tasks.router)
app.include_router(ws.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "autocrew-backend"}
