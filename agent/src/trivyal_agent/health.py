"""Minimal HTTP health server for the agent process."""

import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class HealthServer:
    """Serves GET /health on a configurable port using raw asyncio streams."""

    def __init__(self, port: int) -> None:
        self._port = port
        self._connected = False

    def set_connected(self, value: bool) -> None:
        self._connected = value

    async def serve(self) -> None:
        server = await asyncio.start_server(self._handle, "0.0.0.0", self._port)  # nosec B104
        logger.info("Health server listening on port %d", self._port)
        async with server:
            await server.serve_forever()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            # Read request line and drain headers
            await reader.readline()
            while True:
                line = await reader.readline()
                if line in (b"\r\n", b"\n", b""):
                    break

            status = "connected" if self._connected else "disconnected"
            body = json.dumps({"status": status}).encode()
            response = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(body)}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
            ).encode() + body

            writer.write(response)
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
