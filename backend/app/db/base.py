"""Declarative base and shared mixins for all ORM models.

``Base`` is the single declarative base every model inherits from. The mixins
provide the columns that every table in LedgerIQ shares, keeping the model
definitions DRY and consistent.

Alembic discovers tables via ``Base.metadata``. The full model registry is
imported in ``app.models`` (and pulled in by ``alembic/env.py``) so that
autogenerate sees every table.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Project-wide declarative base."""


class TimestampMixin:
    """Adds ``created_at`` / ``updated_at`` audit columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
