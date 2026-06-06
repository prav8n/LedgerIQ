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
import asyncio
import json
import logging
import re
from dataclasses import dataclass

from app.models.enums import ExpenseCategory
from app.services.llm import LLMClient, get_llm_client

logger = logging.getLogger("ledgeriq.ai")

_MAX_FIELD = 200
_CATEGORY_VALUES = [c.value for c in ExpenseCategory]


def _sanitize(text: str | None, limit: int = _MAX_FIELD) -> str:
    """Collapse whitespace and truncate before putting text in a prompt."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()[:limit]


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


def _parse_category(text: str) -> CategorizationResult | None:
    """Extract a ``{category, confidence}`` object from the model's reply."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        obj = json.loads(text[start : end + 1])
    except (ValueError, TypeError):
        return None
    raw = str(obj.get("category", "")).strip().lower()
    try:
        category = ExpenseCategory(raw)
    except ValueError:
        return None
    try:
        confidence = max(0.0, min(1.0, float(obj.get("confidence", 0.7))))
    except (TypeError, ValueError):
        confidence = 0.7
    return CategorizationResult(category=category, confidence=confidence, source="llm")


class LLMCategorizer(Categorizer):
    """Hybrid categorizer: rule pass first, LLM only for weak results.

    The LLM call runs OFF the request path (a fire-and-forget task) so adding an
    expense never blocks on the network. On success the merchant→category
    mapping is cached back into the keyword map, so the same merchant is a free
    rule hit next time (the existing "learns from corrections" path).
    """

    def __init__(
        self,
        *,
        rule: RuleBasedCategorizer,
        client: LLMClient,
        mapping: dict[str, ExpenseCategory] | None = None,
    ) -> None:
        self._rule = rule
        self._client = client
        # Shared, mutable keyword map that learning writes back into.
        self._mapping = mapping if mapping is not None else MERCHANT_CATEGORY_MAP
        self._llm_cache: dict[str, CategorizationResult] = {}
        self._inflight: set[str] = set()

    async def categorize(
        self,
        *,
        merchant: str | None,
        description: str | None = None,
        amount: float | None = None,
    ) -> CategorizationResult:
        rule_result = await self._rule.categorize(
            merchant=merchant, description=description, amount=amount
        )
        # Strong rule hit -> done (fast, free, no LLM).
        if rule_result.category is not ExpenseCategory.OTHER and rule_result.confidence >= 0.5:
            return rule_result

        key = _sanitize(merchant).lower()
        if not key:
            return rule_result  # nothing stable to key the LLM result on

        cached = self._llm_cache.get(key)
        if cached is not None:
            return cached  # same merchant never hits the LLM twice

        # Kick the LLM off the request path; return the rule result immediately.
        if key not in self._inflight:
            self._inflight.add(key)
            asyncio.create_task(self._classify_and_learn(key, merchant, description))
        return rule_result

    async def _classify_and_learn(
        self, key: str, merchant: str | None, description: str | None
    ) -> None:
        try:
            result = await self._call_llm(merchant, description)
            if result is not None:
                self._llm_cache[key] = result
                self._mapping[key] = result.category  # learn -> future rule hit
                logger.info("LLM categorized %r -> %s", key, result.category.value)
        except Exception:  # never let a background task crash the loop
            logger.exception("LLM categorization failed for %r", key)
        finally:
            self._inflight.discard(key)

    async def _call_llm(
        self, merchant: str | None, description: str | None
    ) -> CategorizationResult | None:
        m, d = _sanitize(merchant), _sanitize(description)
        if not m and not d:
            return None
        system = (
            "You categorize Indian personal-finance transactions. Choose exactly one "
            "category from this list: " + ", ".join(_CATEGORY_VALUES) + ". Respond ONLY "
            'with compact JSON: {"category": "<one>", "confidence": <0..1>}.'
        )
        text = await self._client.complete(
            system=system,
            user=f"Merchant: {m}\nDescription: {d}",
            max_tokens=80,
            temperature=0.0,
        )
        return _parse_category(text)


# Process-wide singleton. Uses the LLM-backed hybrid when a key is configured,
# otherwise the pure rule-based matcher. Callers never change.
def _build_categorizer() -> Categorizer:
    rule = RuleBasedCategorizer()
    client = get_llm_client()
    if client is None:
        return rule
    logger.info("LLM categorization enabled (hybrid)")
    return LLMCategorizer(rule=rule, client=client)


_categorizer: Categorizer = _build_categorizer()


def get_categorizer() -> Categorizer:
    return _categorizer
