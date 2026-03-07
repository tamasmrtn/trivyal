"""Async engine and session factory."""

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from trivyal_hub.config import settings
from trivyal_hub.core.auth import generate_keypair
from trivyal_hub.db.models import HubSettings

engine = create_async_engine(settings.db_url, echo=False)

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def _alembic_config(db_url: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(_MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def _upgrade(cfg: Config) -> None:
    command.upgrade(cfg, "head")


def _stamp(cfg: Config, revision: str) -> None:
    command.stamp(cfg, revision)


async def run_migrations(db_url: str | None = None) -> None:
    """Run Alembic migrations at startup.

    Handles three scenarios transparently:
    - Fresh install: runs all migrations from scratch.
    - Existing pre-Alembic deployment: auto-stamps baseline, then upgrades.
    - Already migrated: upgrade head is a no-op.
    """
    url = db_url or settings.db_url
    cfg = _alembic_config(url)

    eng = create_async_engine(url)
    try:
        async with eng.connect() as conn:
            has_alembic = await conn.scalar(
                text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='alembic_version'")
            )
            has_hub_tables = await conn.scalar(
                text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='hubsettings'")
            )
    finally:
        await eng.dispose()

    if not has_alembic and has_hub_tables:
        # Pre-Alembic deployment: stamp baseline without re-running DDL.
        await asyncio.to_thread(_stamp, cfg, "0001")

    await asyncio.to_thread(_upgrade, cfg)


async def get_hub_settings(session: AsyncSession) -> HubSettings:
    """Return the singleton hub keypair row, creating it on first call."""
    row = await session.get(HubSettings, 1)
    if row is None:
        public_key, private_key = generate_keypair()
        row = HubSettings(public_key=public_key, private_key=private_key)
        session.add(row)
        await session.commit()
    return row


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
