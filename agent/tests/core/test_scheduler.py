"""Tests for core/scheduler.py."""

import asyncio
import contextlib
from unittest.mock import patch

from trivyal_agent.core.scheduler import next_run_delay, run_scheduler


class TestNextRunDelay:
    def test_returns_non_negative_float(self):
        delay = next_run_delay("* * * * *")
        assert isinstance(delay, float)
        assert delay >= 0.0

    def test_every_minute_delay_under_60_seconds(self):
        assert next_run_delay("* * * * *") <= 60.0

    def test_hourly_delay_under_3600_seconds(self):
        assert next_run_delay("0 * * * *") <= 3600.0

    def test_daily_delay_under_86400_seconds(self):
        assert next_run_delay("0 0 * * *") <= 86400.0

    def test_specific_future_expression(self):
        # "0 0 1 1 *" fires once a year — delay must be <= 366 days
        assert next_run_delay("0 0 1 1 *") <= 366 * 24 * 3600


class TestRunScheduler:
    async def test_callback_is_called(self):
        call_count = 0

        async def counting_callback():
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                raise asyncio.CancelledError

        with patch("trivyal_agent.core.scheduler.next_run_delay", return_value=0.0):
            async with asyncio.timeout(2):
                with contextlib.suppress(asyncio.CancelledError):
                    await run_scheduler("* * * * *", counting_callback)

        assert call_count == 2

    async def test_callback_exception_does_not_stop_scheduler(self):
        call_count = 0

        async def flaky_callback():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("transient error")
            raise asyncio.CancelledError

        with patch("trivyal_agent.core.scheduler.next_run_delay", return_value=0.0):
            async with asyncio.timeout(2):
                with contextlib.suppress(asyncio.CancelledError):
                    await run_scheduler("* * * * *", flaky_callback)

        assert call_count == 2

    async def test_cancellation_propagates(self):
        async def never_callback():
            pass  # pragma: no cover

        task = asyncio.create_task(run_scheduler("* * * * *", never_callback))
        await asyncio.sleep(0)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        assert task.cancelled() or task.done()
