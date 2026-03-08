"""WebSocket client — manages the persistent connection to the Trivyal hub."""

import asyncio
import json
import logging

import websockets.asyncio.client as ws_client

from trivyal_agent.config import Settings
from trivyal_agent.core.auth import get_machine_fingerprint, verify_hub_signature
from trivyal_agent.core.cache import clear, list_cached, save
from trivyal_agent.core.docker_client import collect_host_metadata, list_running_images
from trivyal_agent.core.misconfig_runner import run_misconfig_checks
from trivyal_agent.core.scheduler import run_scheduler
from trivyal_agent.core.trivy_runner import scan_all_images
from trivyal_agent.health import HealthServer

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Raised when the hub challenge-response handshake fails."""


class AgentClient:
    """Manages the WebSocket connection lifecycle with the hub."""

    def __init__(self, settings: Settings, health: HealthServer | None = None) -> None:
        self._settings = settings
        self._health = health
        self._ws: ws_client.ClientConnection | None = None

    # ── Public API ────────────────────────────────────────────────────────────

    async def run(self) -> None:
        """Connect to the hub and maintain the connection indefinitely.

        Reconnects with a fixed delay on any transient error.
        """
        while True:
            try:
                await self._connect_and_run()
            except asyncio.CancelledError:
                logger.info("Agent client cancelled — shutting down")
                raise
            except AuthError:
                logger.exception("Authentication failed — check TOKEN and KEY settings")
                await asyncio.sleep(self._settings.reconnect_delay)
            except Exception:
                logger.warning("Connection error — reconnecting in %ds", self._settings.reconnect_delay)
                await asyncio.sleep(self._settings.reconnect_delay)

    # ── Internal lifecycle ────────────────────────────────────────────────────

    async def _connect_and_run(self) -> None:
        ws_url = f"{self._settings.hub_url}/ws/agent"
        headers = {"Authorization": f"Bearer {self._settings.token.get_secret_value()}"}
        logger.info("Connecting to hub at %s", ws_url)

        async with ws_client.connect(ws_url, additional_headers=headers) as ws:
            self._ws = ws
            logger.info("Connected to hub")
            try:
                await self._handshake(ws)
                await self._main_loop(ws)
            finally:
                self._ws = None
                if self._health:
                    self._health.set_connected(False)

    async def _handshake(self, ws: ws_client.ClientConnection) -> None:
        """Complete the hub challenge-response handshake."""
        raw = await ws.recv()
        data = json.loads(raw)

        if data.get("type") != "challenge":
            raise AuthError(f"Expected challenge message, got: {data.get('type')!r}")

        if not verify_hub_signature(
            self._settings.key.get_secret_value(),
            data["signature"],
            data["challenge"],
        ):
            raise AuthError("Hub Ed25519 signature verification failed")

        logger.debug("Hub challenge verified")

        # Send machine fingerprint
        fingerprint = get_machine_fingerprint()
        await ws.send(json.dumps({"type": "fingerprint", "fingerprint": fingerprint}))

        # Send host metadata
        metadata = await collect_host_metadata()
        await ws.send(json.dumps({"type": "host_metadata", "metadata": metadata}))

        # Flush any cached results from previous disconnected period
        await self._flush_cache(ws)

        if self._health:
            self._health.set_connected(True)
        logger.info("Handshake complete")

    async def _main_loop(self, ws: ws_client.ClientConnection) -> None:
        """Handle inbound messages and run the heartbeat + scheduler."""
        heartbeat_task = asyncio.create_task(self._heartbeat_loop(ws))
        scheduler_task = asyncio.create_task(
            run_scheduler(self._settings.scan_schedule, lambda: self._run_scan_cycle(ws))
        )

        try:
            async for raw in ws:
                data = json.loads(raw)
                msg_type = data.get("type")

                if msg_type == "scan_trigger":
                    logger.info("Received on-demand scan trigger from hub")
                    asyncio.create_task(self._run_scan_cycle(ws))

                elif msg_type == "heartbeat_ack":
                    logger.debug("Heartbeat acknowledged by hub")

        finally:
            heartbeat_task.cancel()
            scheduler_task.cancel()
            await asyncio.gather(heartbeat_task, scheduler_task, return_exceptions=True)

    # ── Scanning ──────────────────────────────────────────────────────────────

    async def _run_scan_cycle(self, ws: ws_client.ClientConnection) -> None:
        """Discover containers, scan each with Trivy, and send results to hub."""
        logger.info("Starting scan cycle")
        try:
            containers = await list_running_images()
        except Exception:
            logger.exception("Failed to list running containers")
            return

        if not containers:
            logger.info("No running containers found — nothing to scan")
            return

        # Deduplicate by image name; first container name found wins
        container_map: dict[str, str] = {}
        image_names: list[str] = []
        for c in containers:
            if c["image_name"] not in container_map:
                container_map[c["image_name"]] = c["container_name"]
                image_names.append(c["image_name"])

        logger.info("Found %d container(s) to scan: %s", len(image_names), image_names)
        results = await scan_all_images(image_names)

        for result in results:
            image_name = result.get("ArtifactName", "unknown")
            container_name = container_map.get(image_name)
            save(self._settings.data_dir, image_name, result)
            await self._send_scan_result(ws, result, container_name)

        # Run misconfig checks on all running containers
        try:
            misconfig_results = await run_misconfig_checks()
            for misconfig in misconfig_results:
                await self._send_misconfig_result(ws, misconfig)
        except Exception:
            logger.exception("Failed to run misconfig checks")

    async def _send_scan_result(
        self, ws: ws_client.ClientConnection, result: dict, container_name: str | None = None
    ) -> None:
        try:
            await ws.send(json.dumps({"type": "scan_result", "data": result, "container_name": container_name}))
            logger.info("Sent scan result for %s", result.get("ArtifactName", "unknown"))
        except Exception:
            logger.exception("Failed to send scan result — will retry on reconnect")

    async def _send_misconfig_result(self, ws: ws_client.ClientConnection, result: dict) -> None:
        try:
            await ws.send(json.dumps({"type": "misconfig_result", "data": result}))
            logger.info("Sent misconfig result for %s", result.get("container_name", "unknown"))
        except Exception:
            logger.exception("Failed to send misconfig result")

    async def _flush_cache(self, ws: ws_client.ClientConnection) -> None:
        """Send any cached results from previous disconnected periods."""
        cached = list_cached(self._settings.data_dir)
        if not cached:
            return
        logger.info("Flushing %d cached scan result(s) to hub", len(cached))
        for result in cached:
            image_name = result.get("ArtifactName", "")
            try:
                await ws.send(json.dumps({"type": "scan_result", "data": result, "container_name": None}))
                logger.info("Sent cached result for %s", image_name)
                clear(self._settings.data_dir, image_name)
            except Exception:
                logger.exception("Failed to flush cached result for %s — will retry on reconnect", image_name)

    # ── Heartbeat ─────────────────────────────────────────────────────────────

    async def _heartbeat_loop(self, ws: ws_client.ClientConnection) -> None:
        while True:
            await asyncio.sleep(self._settings.heartbeat_interval)
            try:
                await ws.send(json.dumps({"type": "heartbeat"}))
                logger.debug("Heartbeat sent")
            except Exception:
                logger.warning("Failed to send heartbeat")
                break
