"""Tests for copa_runner — subprocess wrapper."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from trivyal_patcher.copa_runner import run_copa


def _make_mock_proc(lines: list[bytes], returncode: int = 0):
    """Create a mock subprocess with async stdout iteration."""
    mock_proc = MagicMock()

    async def _aiter():
        for line in lines:
            yield line

    mock_proc.stdout = MagicMock()
    mock_proc.stdout.__aiter__ = lambda self: _aiter()
    mock_proc.wait = AsyncMock(return_value=returncode)
    return mock_proc


class TestRunCopa:
    async def test_yields_log_lines_and_completed_result(self):
        mock_proc = _make_mock_proc([b"Patching layer 1\n", b"Patching layer 2\n"], 0)

        with patch("trivyal_patcher.copa_runner.asyncio.create_subprocess_exec", return_value=mock_proc):
            events = [e async for e in run_copa("nginx:1.25", {"Results": []}, "nginx:1.25-patched")]

        log_events = [e for e in events if e["type"] == "log"]
        assert len(log_events) == 2
        assert log_events[0]["line"] == "Patching layer 1"

        result = next(e for e in events if e["type"] == "result")
        assert result["status"] == "completed"
        assert result["patched_tag"] == "nginx:1.25-patched"

    async def test_yields_failed_result_on_nonzero_exit(self):
        mock_proc = _make_mock_proc([b"Error\n"], 1)

        with patch("trivyal_patcher.copa_runner.asyncio.create_subprocess_exec", return_value=mock_proc):
            events = [e async for e in run_copa("nginx:1.25", {}, "nginx:1.25-patched")]

        result = next(e for e in events if e["type"] == "result")
        assert result["status"] == "failed"
        assert "code 1" in result["error"]
