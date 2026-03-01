"""FastAPI app factory and lifespan."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from trivyal_hub.api.v1 import router as v1_router
from trivyal_hub.db.session import create_tables, get_session
from trivyal_hub.ws.manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(title="Trivyal Hub", version="0.1.0", lifespan=lifespan)


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
