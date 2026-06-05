"""Expense categorization.

A rule-based merchant -> category mapper today, structured behind a
``Categorizer`` interface so an LLM-backed implementation can be dropped in
later without touching the call sites.

User overrides: when the caller (the expenses route) is given an explicit
category by the user, it skips categorization entirely and records the expense
as user-categorized. This module only runs when no explicit category exists.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass

from app.models.enums import ExpenseCategory


@dataclass(frozen=True)
class CategorizationResult:
    category: ExpenseCategory
    confidence: float
    source: str  # "rule" | "llm" | "fallback"
    matched_keyword: str | None = None


# Ordered merchant/keyword -> category map. Keys are matched as case-insensitive
# substrings against the merchant name (and description as a fallback). Order
# matters only for readability; matching picks the longest keyword hit.
MERCHANT_CATEGORY_MAP: dict[str, ExpenseCategory] = {
    # Food & dining
    "mcdonald": ExpenseCategory.FOOD,
    "swiggy": ExpenseCategory.FOOD,
    "zomato": ExpenseCategory.FOOD,
    "kfc": ExpenseCategory.FOOD,
    "dominos": ExpenseCategory.FOOD,
    "starbucks": ExpenseCategory.FOOD,
    "burger king": ExpenseCategory.FOOD,
    # Groceries
    "bigbasket": ExpenseCategory.GROCERIES,
    "blinkit": ExpenseCategory.GROCERIES,
    "zepto": ExpenseCategory.GROCERIES,
    "dmart": ExpenseCategory.GROCERIES,
    "instamart": ExpenseCategory.GROCERIES,
    # Shopping
    "amazon": ExpenseCategory.SHOPPING,
    "flipkart": ExpenseCategory.SHOPPING,
    "myntra": ExpenseCategory.SHOPPING,
    "ajio": ExpenseCategory.SHOPPING,
    "nykaa": ExpenseCategory.SHOPPING,
    "meesho": ExpenseCategory.SHOPPING,
    # Travel & transport
    "irctc": ExpenseCategory.TRAVEL,
    "makemytrip": ExpenseCategory.TRAVEL,
    "goibibo": ExpenseCategory.TRAVEL,
    "indigo": ExpenseCategory.TRAVEL,
    "vistara": ExpenseCategory.TRAVEL,
    "uber": ExpenseCategory.TRANSPORT,
    "ola": ExpenseCategory.TRANSPORT,
    "rapido": ExpenseCategory.TRANSPORT,
    "redbus": ExpenseCategory.TRANSPORT,
    # Health
    "apollo": ExpenseCategory.HEALTH,
    "pharmeasy": ExpenseCategory.HEALTH,
    "1mg": ExpenseCategory.HEALTH,
    "netmeds": ExpenseCategory.HEALTH,
    "practo": ExpenseCategory.HEALTH,
    # Entertainment / subscriptions
    "netflix": ExpenseCategory.ENTERTAINMENT,
    "spotify": ExpenseCategory.ENTERTAINMENT,
    "hotstar": ExpenseCategory.ENTERTAINMENT,
    "bookmyshow": ExpenseCategory.ENTERTAINMENT,
    "prime video": ExpenseCategory.ENTERTAINMENT,
    # Utilities
    "jio": ExpenseCategory.UTILITIES,
    "airtel": ExpenseCategory.UTILITIES,
    "vi ": ExpenseCategory.UTILITIES,
    "tata power": ExpenseCategory.UTILITIES,
    "bescom": ExpenseCategory.UTILITIES,
}


class Categorizer(abc.ABC):
    """Strategy interface for assigning a category to an expense.

    The method is async so an LLM/network-backed implementation can be swapped
    in without changing callers (rule-based simply returns synchronously).
    """

    @abc.abstractmethod
    async def categorize(
        self,
        *,
        merchant: str | None,
        description: str | None = None,
        amount: float | None = None,
    ) -> CategorizationResult: ...


class RuleBasedCategorizer(Categorizer):
    """Deterministic keyword/substring matcher over the merchant map."""

    def __init__(self, mapping: dict[str, ExpenseCategory] | None = None) -> None:
        self._mapping = mapping or MERCHANT_CATEGORY_MAP

    async def categorize(
        self,
        *,
        merchant: str | None,
        description: str | None = None,
        amount: float | None = None,
    ) -> CategorizationResult:
        haystack = " ".join(p for p in (merchant, description) if p).lower().strip()
        if not haystack:
            return CategorizationResult(ExpenseCategory.OTHER, 0.0, "fallback")

        # Prefer the longest keyword match for the most specific result.
        best_keyword: str | None = None
        for keyword in self._mapping:
            if keyword in haystack and (
                best_keyword is None or len(keyword) > len(best_keyword)
            ):
                best_keyword = keyword

        if best_keyword is None:
            return CategorizationResult(ExpenseCategory.OTHER, 0.3, "fallback")

        return CategorizationResult(
            category=self._mapping[best_keyword],
            confidence=0.9,
            source="rule",
            matched_keyword=best_keyword.strip(),
        )


# Process-wide singleton. Swap the construction here (e.g. behind a settings
# flag) to introduce an ``LLMCategorizer`` later — callers won't change.
_categorizer: Categorizer = RuleBasedCategorizer()


def get_categorizer() -> Categorizer:
    return _categorizer
