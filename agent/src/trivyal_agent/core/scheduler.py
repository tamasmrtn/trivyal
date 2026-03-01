"""Cron-style scan scheduler.

Runs a callback on the schedule defined by a cron expression. The scheduler
computes the next fire time using *croniter* and sleeps until then.
"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable

from croniter import croniter

logger = logging.getLogger(__name__)


def next_run_delay(cron_expression: str) -> float:
    """Return seconds until the next cron fire time from *now*."""
    cron = croniter(cron_expression, time.time())
    return max(0.0, cron.get_next(float) - time.time())


async def run_scheduler(
    cron_expression: str,
    callback: Callable[[], Awaitable[None]],
) -> None:
    """Run *callback* repeatedly on the given cron schedule.

    This coroutine runs forever (until cancelled). Each iteration computes the
    next fire time, sleeps until then, then calls the callback.
    """
    logger.info("Scheduler starting with expression: %s", cron_expression)
    while True:
        delay = next_run_delay(cron_expression)
        logger.info("Next scheduled scan in %.0f seconds", delay)
        await asyncio.sleep(delay)
        try:
            await callback()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Scheduled scan failed")
