"""FastAPI app factory and lifespan."""

import importlib.metadata
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from trivyal_hub.api.v1 import router as v1_router
from trivyal_hub.config import settings
from trivyal_hub.db.session import engine, get_hub_settings, get_session, run_migrations
from trivyal_hub.ws.manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_migrations()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        await get_hub_settings(session)
    yield


app = FastAPI(title="Trivyal Hub", version=importlib.metadata.version("trivyal-hub"), lifespan=lifespan)


# Health check (no auth)
@app.get("/api/health")
async def health():
    return {"status": "ok"}


# v1 API routes
app.include_router(v1_router)


# WebSocket endpoint for agent connections
@app.websocket("/ws/agent")
async def ws_agent(ws: WebSocket, session: AsyncSession = Depends(get_session)):
    await manager.handle_connection(ws, session)


# Serve the React SPA — mounted last so API routes take precedence.
# Only active when the built UI is present (i.e. in Docker); skipped in dev.
if settings.static_dir.is_dir():
    app.mount("/", StaticFiles(directory=settings.static_dir, html=True), name="ui")
