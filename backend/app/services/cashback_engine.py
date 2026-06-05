"""Backward-compatibility shim.

The cashback engine was generalized into :mod:`app.services.rewards_engine`.
This module re-exports the public names so existing imports keep working.
"""

from __future__ import annotations

from app.services.rewards_engine import (  # noqa: F401
    CashbackResult,
    RewardResult,
    RewardRuleEval,
    RewardsEngine,
    SpendContext,
    get_cashback_engine,
    get_rewards_engine,
)

__all__ = [
    "CashbackResult",
    "RewardResult",
    "RewardRuleEval",
    "RewardsEngine",
    "SpendContext",
    "get_cashback_engine",
    "get_rewards_engine",
]
