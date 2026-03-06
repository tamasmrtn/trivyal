"""Tests for health.py."""

import asyncio
import json
import socket

from trivyal_agent.health import HealthServer


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


async def _request(port: int) -> tuple[int, dict]:
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
    await writer.drain()
    response = await reader.read(4096)
    writer.close()
    await writer.wait_closed()
    status_code = int(response.split(b"\r\n")[0].split()[1])
    body = json.loads(response[response.find(b"\r\n\r\n") + 4 :])
    return status_code, body


class TestHealthServer:
    async def test_returns_200_with_disconnected_status_by_default(self):
        port = _free_port()
        server = HealthServer(port)
        task = asyncio.create_task(server.serve())
        await asyncio.sleep(0.05)
        try:
            status, body = await _request(port)
            assert status == 200
            assert body == {"status": "disconnected"}
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    async def test_returns_connected_after_set_connected(self):
        port = _free_port()
        server = HealthServer(port)
        task = asyncio.create_task(server.serve())
        await asyncio.sleep(0.05)
        server.set_connected(True)
        try:
            status, body = await _request(port)
            assert status == 200
            assert body == {"status": "connected"}
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    async def test_reverts_to_disconnected_on_set_connected_false(self):
        port = _free_port()
        server = HealthServer(port)
        task = asyncio.create_task(server.serve())
        await asyncio.sleep(0.05)
        server.set_connected(True)
        server.set_connected(False)
        try:
            status, body = await _request(port)
            assert status == 200
            assert body == {"status": "disconnected"}
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
