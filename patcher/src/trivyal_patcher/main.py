"""Patcher sidecar entry point."""

import logging

from aiohttp import web

from trivyal_patcher.config import settings
from trivyal_patcher.server import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def main() -> None:
    app = create_app()
    web.run_app(app, port=settings.port)


if __name__ == "__main__":
    main()
