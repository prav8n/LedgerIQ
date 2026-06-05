"""Pytest fixtures.

Forces a throwaway SQLite database and disables the scheduler before any app
module is imported, then recreates the schema fresh for every test.
"""

from __future__ import annotations

import asyncio
import os

# Must be set before importing app.core.config (settings is cached).
os.environ["DATABASE_URL"] = ""
os.environ["SQLITE_PATH"] = "./test_ledgeriq.db"
os.environ["ENABLE_SCHEDULER"] = "false"
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["DEBUG"] = "false"

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402

import app.models  # noqa: E402,F401  -- register all tables on the metadata
from app.db.base import Base  # noqa: E402
from app.db.session import AsyncSessionLocal, engine  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database():
    """Drop and recreate all tables before each test (sync wrapper)."""

    async def _setup() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        # Clear the pool so connections aren't bound to this throwaway loop.
        await engine.dispose()

    asyncio.run(_setup())
    yield


@pytest_asyncio.fixture
async def db():
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
