"""Tests for main.py — agent entrypoint validation and startup."""

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
            patch("trivyal_agent.main.AgentClient") as mock_client_cls,
        ):
            mock_client_cls.return_value.run = AsyncMock()

            await _main()

        assert data_dir.exists()
        mock_client_cls.assert_called_once()
