"""Trivyal agent entrypoint."""

import asyncio
import logging
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
    await asyncio.gather(health.serve(), client.run())


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
