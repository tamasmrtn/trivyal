"""
SimulatedAgent — implements the hub WebSocket protocol for integration tests.

Speaks the exact same protocol as the real trivyal_agent.ws.client, allowing
the hub to be tested end-to-end without needing a real agent binary or Trivy.

Hub WebSocket protocol (from ws/manager.py):
  Hub → Agent: {"type": "challenge", "challenge": "<hex 32B>", "signature": "<hex>"}
  Agent → Hub: {"type": "fingerprint", "fingerprint": "<hex 64 chars>"}
  Agent → Hub: {"type": "host_metadata", "metadata": {...}}
  Hub → Agent: {"type": "scan_trigger"}
  Agent → Hub: {"type": "scan_result", "data": <trivy JSON>}
  Agent → Hub: {"type": "heartbeat"}
  Hub → Agent: {"type": "heartbeat_ack"}
"""

import asyncio
import json
from base64 import b64decode

import websockets
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from helpers.trivy_fixtures import SCAN_V1

# Deterministic test fingerprint (64 hex chars = 32 bytes).
_TEST_FINGERPRINT = "a" * 64

_TEST_METADATA = {
    "hostname": "test-host",
    "os": "Linux",
    "docker_version": "27.0.0",
    "agent_version": "0.1.0",
}


class AuthError(Exception):
    """Raised when the hub sends an invalid challenge signature."""


class SimulatedAgent:
    """
    Simulates an agent connecting to the hub over WebSocket.

    Usage::

        agent = SimulatedAgent(ws_url, token, hub_public_key)
        await agent.connect_and_handshake()
        # ... run tests ...
        await agent.close()

    Or use the ``connected_agent`` pytest fixture from conftest.py.
    """

    def __init__(self, hub_ws_url: str, token: str, hub_public_key: str) -> None:
        self._url = hub_ws_url
        self._token = token
        self._hub_public_key = hub_public_key  # base64-encoded Ed25519 public key
        self._ws = None

    # ── Connection lifecycle ───────────────────────────────────────────────────

    async def connect_and_handshake(self) -> None:
        """Open WebSocket and complete the full challenge/fingerprint/metadata exchange."""
        self._ws = await websockets.connect(
            self._url,
            additional_headers={"Authorization": f"Bearer {self._token}"},
        )

        # Step 1: receive and verify the hub's challenge
        raw = await asyncio.wait_for(self._ws.recv(), timeout=10.0)
        msg = json.loads(raw)
        if msg.get("type") != "challenge":
            raise AuthError(f"Expected 'challenge' message, got: {msg.get('type')!r}")
        self._verify_hub_challenge(msg["challenge"], msg["signature"])

        # Step 2: send fingerprint
        await self._ws.send(json.dumps({"type": "fingerprint", "fingerprint": _TEST_FINGERPRINT}))

        # Step 3: send host metadata
        await self._ws.send(json.dumps({"type": "host_metadata", "metadata": _TEST_METADATA}))

    async def close(self) -> None:
        if self._ws:
            await self._ws.close()
            self._ws = None

    # ── Protocol helpers ───────────────────────────────────────────────────────

    def _verify_hub_challenge(self, challenge_hex: str, signature_hex: str) -> None:
        """Verify the hub's Ed25519 signature on the challenge bytes."""
        raw_key = b64decode(self._hub_public_key)
        verify_key = VerifyKey(raw_key)
        try:
            verify_key.verify(
                bytes.fromhex(challenge_hex),
                bytes.fromhex(signature_hex),
            )
        except BadSignatureError as exc:
            raise AuthError("Hub sent invalid challenge signature") from exc

    async def recv_message(self, timeout: float = 10.0) -> dict:
        """Receive and parse a single JSON message from the hub."""
        raw = await asyncio.wait_for(self._ws.recv(), timeout=timeout)
        return json.loads(raw)

    async def send_heartbeat(self) -> None:
        await self._ws.send(json.dumps({"type": "heartbeat"}))

    async def recv_heartbeat_ack(self, timeout: float = 5.0) -> None:
        """Send a heartbeat and wait for the hub's ack."""
        await self.send_heartbeat()
        msg = await self.recv_message(timeout=timeout)
        assert msg.get("type") == "heartbeat_ack", f"Expected heartbeat_ack, got {msg}"

    async def handle_scan_trigger_and_respond(self, scan_data: dict | None = None) -> None:
        """
        Wait for a scan_trigger message from the hub, then respond with scan_result.

        This must typically run concurrently with the HTTP call that triggers
        the scan — see conftest usage with asyncio.gather / asyncio.create_task.
        """
        msg = await self.recv_message(timeout=15.0)
        assert msg.get("type") == "scan_trigger", f"Expected scan_trigger, got {msg}"
        await self._ws.send(
            json.dumps(
                {
                    "type": "scan_result",
                    "data": scan_data if scan_data is not None else SCAN_V1,
                }
            )
        )
