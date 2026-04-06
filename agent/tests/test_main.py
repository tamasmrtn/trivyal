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

        # Make gather return immediately by raising CancelledError
        async def _fake_gather(*coros, **kwargs):
            for c in coros:
                c.close()
            raise asyncio.CancelledError

        with (
            patch("trivyal_agent.main.settings", settings),
            patch("trivyal_agent.main.HealthServer") as mock_health_cls,
            patch("trivyal_agent.main.AgentClient") as mock_client_cls,
            patch("trivyal_agent.main.asyncio.gather", side_effect=_fake_gather),
        ):
            mock_health_cls.return_value.serve = AsyncMock()
            mock_client_cls.return_value.run = AsyncMock()

            with pytest.raises(asyncio.CancelledError):
                await _main()

        assert data_dir.exists()
        mock_client_cls.assert_called_once()
        mock_health_cls.assert_called_once_with(settings.health_port)
