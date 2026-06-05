"""User account model — the root of all user-scoped data."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.budget import Budget
    from app.models.credit_card import CreditCard
    from app.models.emi import EMI
    from app.models.expense import Expense
    from app.models.goal import Goal
    from app.models.income import Income
    from app.models.investment import Investment
    from app.models.monthly_summary import MonthlySummary
    from app.models.net_worth import NetWorthSnapshot
    from app.models.notification import Notification
    from app.models.subscription import Subscription


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(20))

    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    locale: Mapped[str] = mapped_column(String(10), default="en-IN", nullable=False)
    timezone: Mapped[str] = mapped_column(
        String(40), default="Asia/Kolkata", nullable=False
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ------------------------------------------------------------ relations
    incomes: Mapped[list["Income"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    credit_cards: Mapped[list["CreditCard"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    budgets: Mapped[list["Budget"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    goals: Mapped[list["Goal"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    investments: Mapped[list["Investment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    emis: Mapped[list["EMI"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    monthly_summaries: Mapped[list["MonthlySummary"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    net_worth_snapshots: Mapped[list["NetWorthSnapshot"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email!r}>"
