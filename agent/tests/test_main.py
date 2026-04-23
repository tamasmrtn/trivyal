"""Tests for main.py — agent entrypoint validation and startup."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from trivyal_agent.config import Settings


def _make_settings(**overrides) -> Settings:
    defaults = {
        "hub_url": "ws://localhost:8099",
        "token": "test-token",
        "key": "dGVzdC1rZXktYmFzZTY0LWVuY29kZWQtMzJieXRlcw==",
        "scan_schedule": "0 2 * * *",
        "heartbeat_interval": 30,
        "reconnect_delay": 1,
    }
    defaults.update(overrides)
    return Settings(**defaults)


class TestMainEntrypoint:
    async def test_exits_when_token_missing(self, tmp_path):
        from trivyal_agent.main import _main

        settings = _make_settings(token="", data_dir=str(tmp_path))
        with (
            patch("trivyal_agent.main.settings", settings),
            pytest.raises(SystemExit, match="1"),
        ):
            await _main()

    async def test_exits_when_key_missing(self, tmp_path):
        from trivyal_agent.main import _main

        settings = _make_settings(key="", data_dir=str(tmp_path))
        with (
            patch("trivyal_agent.main.settings", settings),
            pytest.raises(SystemExit, match="1"),
        ):
            await _main()

    async def test_creates_data_dir_and_starts(self, tmp_path):
        from trivyal_agent.main import _main

        data_dir = tmp_path / "agent-data"
        settings = _make_settings(data_dir=str(data_dir))

        with (
            patch("trivyal_agent.main.settings", settings),
            patch("trivyal_agent.main.HealthServer") as mock_health_cls,
            patch("trivyal_agent.main.AgentClient") as mock_client_cls,
        ):
            # Work tasks complete immediately — _main exits cleanly
            mock_health_cls.return_value.serve = AsyncMock()
            mock_client_cls.return_value.run = AsyncMock()

            await _main()

        assert data_dir.exists()
        mock_client_cls.assert_called_once()
        mock_health_cls.assert_called_once_with(settings.health_port)

    async def test_shutdown_event_cancels_pending_tasks(self, tmp_path):
        """When the shutdown event is set, pending work tasks are cancelled."""
        from trivyal_agent.main import _main

        settings = _make_settings(data_dir=str(tmp_path))
        cancelled = asyncio.Event()

        with (
            patch("trivyal_agent.main.settings", settings),
            patch("trivyal_agent.main.HealthServer") as mock_health_cls,
            patch("trivyal_agent.main.AgentClient") as mock_client_cls,
        ):

            async def _block_then_track_cancel():
                try:
                    await asyncio.sleep(3600)
                except asyncio.CancelledError:
                    cancelled.set()

            mock_health_cls.return_value.serve = AsyncMock(side_effect=_block_then_track_cancel)
            mock_client_cls.return_value.run = AsyncMock(side_effect=_block_then_track_cancel)

            # Patch the shutdown_event to auto-set after a tick
            original_event_cls = asyncio.Event

            class _AutoSetEvent(original_event_cls):
                def __init__(self):
                    super().__init__()

                async def wait(self):
                    await asyncio.sleep(0.01)
                    self.set()

            with patch("trivyal_agent.main.asyncio.Event", _AutoSetEvent):
                await _main()

        assert cancelled.is_set()
