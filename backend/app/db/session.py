"""Async SQLAlchemy engine and session management.

Exposes:
- ``engine``        : the process-wide async engine.
- ``AsyncSessionLocal`` : an async session factory.
- ``get_db``        : a FastAPI dependency yielding a request-scoped session.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


def _build_engine() -> AsyncEngine:
    """Create an async engine tuned for the configured backend.

    SQLite does not support connection pool sizing arguments, so we only pass
    pool tuning when talking to a real (Postgres) server.
    """
    assert settings.DATABASE_URL is not None

    if settings.is_sqlite:
        return create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DB_ECHO,
            future=True,
            connect_args={"check_same_thread": False},
        )

    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        future=True,
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
    )


engine: AsyncEngine = _build_engine()

if settings.is_sqlite:
    # SQLite ignores foreign keys unless explicitly enabled per connection, so
    # ON DELETE SET NULL / CASCADE only fire when this pragma is set.
    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_fks(dbapi_connection, _record) -> None:  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a transactional session.

    The session is committed if the request handler succeeds and rolled back
    if any exception propagates, then always closed.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
