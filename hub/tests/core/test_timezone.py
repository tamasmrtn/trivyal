"""Tests for timezone configuration."""

from unittest.mock import patch
from zoneinfo import ZoneInfo

from trivyal_hub.config import Settings
from trivyal_hub.db.models import _now


class TestSettings:
    def test_default_timezone_is_utc(self):
        s = Settings()
        assert s.tz == "UTC"

    def test_reads_trivyal_tz_env_var(self, monkeypatch):
        monkeypatch.setenv("TRIVYAL_TZ", "Europe/Amsterdam")
        s = Settings()
        assert s.tz == "Europe/Amsterdam"


class TestNow:
    def test_returns_timezone_aware_datetime(self):
        dt = _now()
        assert dt.tzinfo is not None

    def test_default_tz_is_utc(self):
        dt = _now()
        assert dt.utcoffset().total_seconds() == 0

    def test_uses_configured_timezone(self):
        from trivyal_hub.config import settings

        with patch.object(settings, "tz", "Europe/Amsterdam"):
            dt = _now()

        assert dt.tzinfo == ZoneInfo("Europe/Amsterdam")

    def test_different_timezones_produce_correct_offset(self):
        from trivyal_hub.config import settings

        with patch.object(settings, "tz", "US/Eastern"):
            dt = _now()

        assert dt.tzinfo == ZoneInfo("US/Eastern")
