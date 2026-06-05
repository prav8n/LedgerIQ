"""Model registry.

Importing this package imports every ORM model, which registers them on
``Base.metadata``. Alembic's ``env.py`` imports this module so that
autogenerate can see the full schema.
"""

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
from app.models.reward_rule import RewardRule
from app.models.subscription import Subscription
from app.models.user import User

__all__ = [
    "Budget",
    "CreditCard",
    "EMI",
    "Expense",
    "Goal",
    "Income",
    "Investment",
    "MonthlySummary",
    "NetWorthSnapshot",
    "Notification",
    "RewardRule",
    "Subscription",
    "User",
]
