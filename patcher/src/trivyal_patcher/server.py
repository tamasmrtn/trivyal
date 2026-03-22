"""HTTP server for the patcher sidecar."""

import asyncio
import json
import logging

from aiohttp import web

from trivyal_patcher.config import settings
from trivyal_patcher.container_ops import restart_container
from trivyal_patcher.copa_runner import run_copa
from trivyal_patcher.docker_client import DockerClient

logger = logging.getLogger(__name__)


async def health(_request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def patch(request: web.Request) -> web.StreamResponse:
    body = await request.json()
    image = body.get("image")
    trivy_report = body.get("trivy_report")
    patched_tag = body.get("patched_tag")

    if not image or not trivy_report or not patched_tag:
        return web.json_response(
            {"error": "image, trivy_report, and patched_tag are required"},
            status=400,
        )

    response = web.StreamResponse(
        status=200,
        headers={"Content-Type": "application/x-ndjson"},
    )
    await response.prepare(request)

    async for event in run_copa(image, trivy_report, patched_tag):
        line = json.dumps(event) + "\n"
        await response.write(line.encode())

    await response.write_eof()
    return response


async def restart(request: web.Request) -> web.Response:
    body = await request.json()
    container_id = body.get("container_id")
    image = body.get("image")

    if not container_id or not image:
        return web.json_response(
            {"error": "container_id and image are required"},
            status=400,
        )

    docker = DockerClient(settings.docker_socket)
    result = await asyncio.to_thread(restart_container, docker, container_id, image)
    return web.json_response(result)


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_post("/patch", patch)
    app.router.add_post("/restart", restart)
    return app
