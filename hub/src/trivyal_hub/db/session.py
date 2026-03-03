"""Async engine and session factory."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from trivyal_hub.config import settings
from trivyal_hub.core.auth import generate_keypair
from trivyal_hub.db.models import HubSettings

engine = create_async_engine(settings.db_url, echo=False)


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


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
