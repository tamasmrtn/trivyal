"""Tests for the Alembic migration framework."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from trivyal_hub.db.session import run_migrations


class TestMigrations:
    async def test_fresh_install(self, tmp_path):
        """Fresh DB: upgrade head creates all tables and stamps version at head."""
        db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"

        await run_migrations(db_url=db_url)

        eng = create_async_engine(db_url)
        try:
            async with eng.connect() as conn:
                tables = set(await conn.run_sync(lambda c: c.dialect.get_table_names(c)))
                assert "hubsettings" in tables
                assert "agent" in tables
                assert "container" in tables
                assert "scanresult" in tables
                assert "finding" in tables
                assert "riskacceptance" in tables
                assert "misconfigfinding" in tables
                assert "alembic_version" in tables

                version = await conn.scalar(text("SELECT version_num FROM alembic_version"))
                assert version == "0006"
        finally:
            await eng.dispose()

    async def test_existing_deployment(self, tmp_path):
        """Pre-Alembic DB: auto-stamps baseline, applies any new migrations, no error."""
        db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"

        # Simulate a pre-Alembic deployment — create tables directly
        eng = create_async_engine(db_url)
        async with eng.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        await eng.dispose()

        # run_migrations should detect the existing tables and stamp without errors
        await run_migrations(db_url=db_url)

        eng = create_async_engine(db_url)
        try:
            async with eng.connect() as conn:
                version = await conn.scalar(text("SELECT version_num FROM alembic_version"))
                assert version == "0006"
        finally:
            await eng.dispose()
