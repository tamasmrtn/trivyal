"""WebSocket connection manager for agents."""

import logging
import secrets
from datetime import UTC, datetime

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from trivyal_hub.core.aggregator import process_scan_result
from trivyal_hub.core.auth import sign_challenge, verify_token
from trivyal_hub.db.models import Agent, AgentStatus
from trivyal_hub.db.session import get_hub_settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}  # agent_id -> websocket

    async def authenticate(self, ws: WebSocket, session: AsyncSession) -> Agent | None:
        """Validate the agent token from the WebSocket headers and run the challenge handshake."""
        token = ws.headers.get("authorization", "").removeprefix("Bearer ").strip()
        if not token:
            return None

        # Find agent by matching token hash
        agents = (await session.execute(select(Agent))).scalars().all()
        agent = next((a for a in agents if verify_token(token, a.token_hash)), None)
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
        self.active[agent_id] = ws

    def disconnect(self, agent_id: str):
        self.active.pop(agent_id, None)

    async def send_scan_trigger(self, agent_id: str) -> bool:
        ws = self.active.get(agent_id)
        if not ws:
            return False
        try:
            await ws.send_json({"type": "scan_trigger"})
            return True
        except Exception:
            logger.exception("Failed to send scan trigger to agent %s", agent_id)
            return False

    async def handle_connection(self, ws: WebSocket, session: AsyncSession):
        """Full lifecycle of an agent WebSocket connection."""
        await ws.accept()

        agent = await self.authenticate(ws, session)
        if not agent:
            await ws.close(code=4001, reason="Authentication failed")
            return

        await self.connect(agent.id, ws)
        agent.status = AgentStatus.ONLINE
        agent.last_seen = datetime.now(UTC)
        session.add(agent)
        await session.commit()

        logger.info("Agent %s (%s) connected", agent.name, agent.id)

        try:
            while True:
                data = await ws.receive_json()
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
                    agent.last_seen = datetime.now(UTC)
                    session.add(agent)
                    await session.commit()

                elif msg_type == "scan_result":
                    scan_data = data.get("data", {})
                    await process_scan_result(session, agent.id, scan_data)

                    # Refresh to avoid stale ORM state: trigger_scan sets SCANNING
                    # in a separate session; without a refresh, SQLAlchemy sees no
                    # change from ONLINE→ONLINE and skips the UPDATE.
                    await session.refresh(agent)
                    agent.status = AgentStatus.ONLINE
                    agent.last_seen = datetime.now(UTC)
                    session.add(agent)
                    await session.commit()

                elif msg_type == "heartbeat":
                    agent.last_seen = datetime.now(UTC)
                    session.add(agent)
                    await session.commit()
                    await ws.send_json({"type": "heartbeat_ack"})

        except WebSocketDisconnect:
            logger.info("Agent %s disconnected", agent.name)
        finally:
            self.disconnect(agent.id)
            agent.status = AgentStatus.OFFLINE
            agent.last_seen = datetime.now(UTC)
            session.add(agent)
            await session.commit()


manager = ConnectionManager()
