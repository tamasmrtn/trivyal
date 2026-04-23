"""FastAPI app factory and lifespan."""

import asyncio
import importlib.metadata
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import Depends, FastAPI, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

from trivyal_hub.api.v1 import router as v1_router
from trivyal_hub.config import settings
from trivyal_hub.core.acceptance_expiry import expire_stale_acceptances
from trivyal_hub.db.session import engine, get_hub_settings, get_session, run_migrations
from trivyal_hub.ws.manager import manager

logger = logging.getLogger(__name__)


async def _acceptance_expiry_loop() -> None:
    while True:
        try:
            async with AsyncSession(engine, expire_on_commit=False) as session:
                count = await expire_stale_acceptances(session)
            if count:
                logger.info("Expired %d stale risk acceptance(s)", count)
        except Exception:
            logger.exception("Error during acceptance expiry run")
        await asyncio.sleep(settings.acceptance_expiry_interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    await run_migrations()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        await get_hub_settings(session)
    task = asyncio.create_task(_acceptance_expiry_loop())
    await manager.start_monitor()
    yield
    await manager.stop_monitor()
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


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


class SPAStaticFiles(StaticFiles):
    """Serve index.html for any path that doesn't match a real static file."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except Exception:
            return await super().get_response("index.html", scope)


# Serve the React SPA — mounted last so API routes take precedence.
# Only active when the built UI is present (i.e. in Docker); skipped in dev.
if settings.static_dir.is_dir():
    app.mount("/", SPAStaticFiles(directory=settings.static_dir, html=True), name="ui")
