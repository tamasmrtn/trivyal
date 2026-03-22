"""In-memory log buffer for streaming patch logs via SSE."""

import asyncio
import logging

logger = logging.getLogger(__name__)


class LogBuffer:
    """Per-request log queues for SSE streaming."""

    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue] = {}

    def subscribe(self, request_id: str) -> asyncio.Queue:
        if request_id not in self._queues:
            self._queues[request_id] = asyncio.Queue()
        return self._queues[request_id]

    async def publish(self, request_id: str, line: str) -> None:
        queue = self._queues.get(request_id)
        if queue:
            await queue.put(line)

    async def complete(self, request_id: str) -> None:
        queue = self._queues.get(request_id)
        if queue:
            await queue.put(None)  # sentinel
            # Schedule cleanup after a short delay to let consumers drain
            asyncio.get_event_loop().call_later(5.0, self._cleanup, request_id)

    def _cleanup(self, request_id: str) -> None:
        self._queues.pop(request_id, None)


log_buffer = LogBuffer()
