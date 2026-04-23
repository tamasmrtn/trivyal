"""Trivyal agent entrypoint."""

import asyncio
import logging
import signal
import sys

from trivyal_agent.config import settings
from trivyal_agent.health import HealthServer
from trivyal_agent.ws.client import AgentClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


async def _main() -> None:
    if not settings.token.get_secret_value():
        logger.error("TRIVYAL_TOKEN is not set — cannot connect to hub")
        sys.exit(1)

    if not settings.key.get_secret_value():
        logger.error("TRIVYAL_KEY is not set — cannot verify hub identity")
        sys.exit(1)

    settings.data_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Trivyal agent v%s starting — hub: %s  schedule: %s",
        settings.agent_version,
        settings.hub_url,
        settings.scan_schedule,
    )

    health = HealthServer(settings.health_port)
    client = AgentClient(settings, health=health)

    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda s=sig: (
                logger.info("Received %s — initiating graceful shutdown", signal.Signals(s).name),
                shutdown_event.set(),
            ),
        )

    shutdown_task = asyncio.create_task(shutdown_event.wait())
    health_task = asyncio.create_task(health.serve())
    client_task = asyncio.create_task(client.run())

    tasks = {shutdown_task, health_task, client_task}
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    for t in pending:
        t.cancel()
    await asyncio.gather(*pending, return_exceptions=True)

    logger.info("Agent shut down cleanly")


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
