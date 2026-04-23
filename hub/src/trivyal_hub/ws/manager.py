"""WebSocket connection manager for agents."""

import asyncio
import contextlib
import logging
import secrets
import time
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from trivyal_hub.config import settings
from trivyal_hub.core.aggregator import process_scan_result
from trivyal_hub.core.auth import hash_token, sign_challenge
from trivyal_hub.core.misconfig_aggregator import process_misconfig_result
from trivyal_hub.db.models import Agent, AgentStatus, _now
from trivyal_hub.db.session import get_hub_settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}  # agent_id -> websocket
        self.last_seen: dict[str, float] = {}  # agent_id -> monotonic timestamp
        self._monitor_task: asyncio.Task | None = None
        self._auth_failures: defaultdict[str, list[float]] = defaultdict(list)

    def is_rate_limited(self, client_ip: str) -> bool:
        """Check if an IP has exceeded the auth failure rate limit."""
        now = time.monotonic()
        window = settings.auth_rate_window
        # Prune old entries
        self._auth_failures[client_ip] = [t for t in self._auth_failures[client_ip] if now - t < window]
        return len(self._auth_failures[client_ip]) >= settings.auth_rate_limit

    def record_auth_failure(self, client_ip: str):
        """Record a failed authentication attempt for rate limiting."""
        self._auth_failures[client_ip].append(time.monotonic())

    async def authenticate(self, ws: WebSocket, session: AsyncSession) -> Agent | None:
        """Validate the agent token from the WebSocket headers and run the challenge handshake."""
        token = ws.headers.get("authorization", "").removeprefix("Bearer ").strip()
        if not token:
            return None

        # Find agent by direct token_hash lookup (O(1) with index)
        token_hash = hash_token(token)
        agent = (await session.execute(select(Agent).where(Agent.token_hash == token_hash))).scalar_one_or_none()
        if not agent:
            return None

        # Challenge-response: hub signs a random challenge, agent verifies
        hub_settings = await get_hub_settings(session)
        challenge = secrets.token_bytes(32)
        signature = sign_challenge(hub_settings.private_key, challenge)
        await ws.send_json(
            {
                "type": "challenge",
                "challenge": challenge.hex(),
                "signature": signature.hex(),
            }
        )

        return agent

    async def connect(self, agent_id: str, ws: WebSocket):
        # Store new ws first so ws1's finally-block disconnect() doesn't evict ws2.
        old = self.active.pop(agent_id, None)
        self.active[agent_id] = ws
        self.last_seen[agent_id] = time.monotonic()
        if old is not None:
            with contextlib.suppress(Exception):
                await old.close(code=4000, reason="Superseded by new connection")

    def disconnect(self, agent_id: str, ws: WebSocket):
        # Only remove if this ws is still the registered one; guards against ws1's
        # finally evicting ws2 when a rapid reconnect races with ongoing processing.
        if self.active.get(agent_id) is ws:
            self.active.pop(agent_id)
            self.last_seen.pop(agent_id, None)

    async def send_scan_trigger(self, agent_id: str) -> bool:
        ws = self.active.get(agent_id)
        if not ws:
            return False
        try:
            await ws.send_json({"type": "scan_trigger"})
            return True
        except Exception:
            logger.exception("Failed to send scan trigger to agent %s", agent_id)
            # Remove the broken ws so subsequent receive_json() isn't left with
            # application_state=DISCONNECTED (set synchronously by Starlette's send()).
            self.disconnect(agent_id, ws)
            return False

    async def handle_connection(self, ws: WebSocket, session: AsyncSession):
        """Full lifecycle of an agent WebSocket connection."""
        await ws.accept()

        client_ip = ws.client.host if ws.client else "unknown"
        if self.is_rate_limited(client_ip):
            logger.warning("Rate limited connection from %s", client_ip)
            await ws.close(code=4004, reason="Rate limited")
            return

        agent = await self.authenticate(ws, session)
        if not agent:
            self.record_auth_failure(client_ip)
            await ws.close(code=4001, reason="Authentication failed")
            return

        await self.connect(agent.id, ws)
        agent.status = AgentStatus.ONLINE
        agent.last_seen = _now()
        session.add(agent)
        await session.commit()

        logger.info("Agent %s (%s) connected", agent.name, agent.id)

        try:
            while True:
                try:
                    data = await asyncio.wait_for(ws.receive_json(), timeout=settings.heartbeat_timeout)
                except TimeoutError:
                    logger.warning(
                        "Agent %s timed out (no message in %ds)",
                        agent.name,
                        settings.heartbeat_timeout,
                    )
                    break
                self.last_seen[agent.id] = time.monotonic()
                msg_type = data.get("type")

                if msg_type == "fingerprint":
                    fingerprint = data.get("fingerprint")
                    if agent.fingerprint and agent.fingerprint != fingerprint:
                        await ws.close(code=4003, reason="Fingerprint mismatch")
                        break
                    if not agent.fingerprint:
                        agent.fingerprint = fingerprint
                        session.add(agent)
                        await session.commit()

                elif msg_type == "host_metadata":
                    agent.host_metadata = data.get("metadata")
                    agent.last_seen = _now()
                    session.add(agent)
                    await session.commit()

                elif msg_type == "scan_result":
                    scan_data = data.get("data", {})
                    container_name = data.get("container_name")
                    await process_scan_result(session, agent.id, scan_data, container_name)

                    # Refresh to avoid stale ORM state: trigger_scan sets SCANNING
                    # in a separate session; without a refresh, SQLAlchemy sees no
                    # change from ONLINE→ONLINE and skips the UPDATE.
                    await session.refresh(agent)
                    agent.status = AgentStatus.ONLINE
                    agent.last_seen = _now()
                    session.add(agent)
                    await session.commit()

                elif msg_type == "misconfig_result":
                    misconfig_data = data.get("data", {})
                    await process_misconfig_result(session, agent.id, misconfig_data)
                    agent.last_seen = _now()
                    session.add(agent)
                    await session.commit()

                elif msg_type == "heartbeat":
                    agent.last_seen = _now()
                    session.add(agent)
                    await session.commit()
                    await ws.send_json({"type": "heartbeat_ack"})

        except WebSocketDisconnect:
            logger.info("Agent %s disconnected", agent.name)
        except RuntimeError:
            # Starlette sets application_state=DISCONNECTED synchronously inside
            # close() before the actual send completes.  If connect() closes the
            # old WebSocket while this coroutine is awaiting a DB operation, the
            # next receive_json() check fires RuntimeError instead of raising
            # WebSocketDisconnect.  Treat it as a normal disconnect.
            logger.info("Agent %s lost connection", agent.name)
        finally:
            self.disconnect(agent.id, ws)
            # Only mark offline if no replacement ws registered.  If ws2
            # superseded this connection, ws2 already wrote ONLINE; writing
            # OFFLINE here would clobber it.  The identity check in disconnect()
            # tells us: if agent.id is gone from active, this was the last ws.
            if agent.id not in self.active:
                agent.status = AgentStatus.OFFLINE
                agent.last_seen = _now()
                session.add(agent)
                await session.commit()

    # ── Heartbeat monitor ──────────────────────────────────────────────────

    async def start_monitor(self):
        """Start the background task that closes stale agent connections."""
        self._monitor_task = asyncio.create_task(self._monitor_agents())

    async def stop_monitor(self):
        """Cancel the background monitor task."""
        if self._monitor_task:
            self._monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitor_task

    async def _monitor_agents(self):
        """Periodically close WebSockets that haven't sent any message recently."""
        while True:
            await asyncio.sleep(30)
            await self._monitor_agents_once()

    async def _monitor_agents_once(self):
        """Single pass: close any WebSocket that hasn't been heard from recently."""
        now = time.monotonic()
        for agent_id, ws in list(self.active.items()):
            last = self.last_seen.get(agent_id, 0)
            if now - last > settings.heartbeat_timeout:
                logger.warning("Agent %s heartbeat timeout — closing connection", agent_id)
                with contextlib.suppress(Exception):
                    await ws.close(code=4002, reason="Heartbeat timeout")


manager = ConnectionManager()
