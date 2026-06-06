"""Tests for the LLM-backed AI services using a mocked LLM client."""

from __future__ import annotations

import asyncio
from datetime import date

from app.core.security import hash_password
from app.models.enums import ExpenseCategory
from app.models.user import User
from app.services.categorization_service import (
    LLMCategorizer,
    RuleBasedCategorizer,
)
from app.services.insights_service import (
    LLMInsightGenerator,
    RuleBasedInsightGenerator,
)
from app.services.llm.base import LLMClient, LLMError


class FakeLLM(LLMClient):
    """Records calls and returns a canned response (or raises)."""

    def __init__(self, response: str = "", *, fail: bool = False) -> None:
        self.model = "fake"
        self._response = response
        self._fail = fail
        self.calls = 0

    async def complete(self, *, system, user, max_tokens=1024, temperature=0.0) -> str:
        self.calls += 1
        if self._fail:
            raise LLMError("boom")
        return self._response


# --------------------------------------------------------------- categorizer
async def test_strong_rule_skips_llm():
    fake = FakeLLM('{"category":"shopping","confidence":0.9}')
    rule = RuleBasedCategorizer(mapping={"swiggy": ExpenseCategory.FOOD})
    cat = LLMCategorizer(rule=rule, client=fake, mapping={"swiggy": ExpenseCategory.FOOD})

    res = await cat.categorize(merchant="Swiggy")
    assert res.category is ExpenseCategory.FOOD
    assert res.source == "rule"
    assert fake.calls == 0  # LLM never called for a confident rule hit


async def test_llm_runs_off_path_and_learns():
    fake = FakeLLM('{"category":"shopping","confidence":0.92}')
    shared: dict[str, ExpenseCategory] = {}  # empty -> rule returns OTHER
    cat = LLMCategorizer(
        rule=RuleBasedCategorizer(mapping=shared), client=fake, mapping=shared
    )

    # First sighting: returns the (weak) rule result immediately, LLM in background.
    first = await cat.categorize(merchant=" NewMerchant Pvt ")
    assert first.category is ExpenseCategory.OTHER  # did not block on the network
    await asyncio.sleep(0.05)  # let the background task finish

    assert fake.calls == 1
    assert shared.get("newmerchant pvt") is ExpenseCategory.SHOPPING  # learned

    # Second sighting: resolved from cache/learned map, no second LLM call.
    second = await cat.categorize(merchant="NewMerchant Pvt")
    assert second.category is ExpenseCategory.SHOPPING
    assert fake.calls == 1


async def test_llm_failure_falls_back_silently():
    fake = FakeLLM(fail=True)
    shared: dict[str, ExpenseCategory] = {}
    cat = LLMCategorizer(rule=RuleBasedCategorizer(mapping=shared), client=fake, mapping=shared)

    res = await cat.categorize(merchant="Unknownco")
    assert res.category is ExpenseCategory.OTHER
    await asyncio.sleep(0.05)
    assert fake.calls == 1
    assert shared == {}  # nothing learned on failure


# ----------------------------------------------------------------- insights
async def _user(db) -> User:
    u = User(email="ai@example.com", hashed_password=hash_password("x"))
    db.add(u)
    await db.flush()
    return u


async def test_insights_llm_used_and_cached(db):
    user = await _user(db)
    fake = FakeLLM(
        '[{"type":"tip","category":"savings","title":"Save more",'
        '"description":"You could save ₹5,000 more this month.","metric":"+₹5,000"}]'
    )
    gen = LLMInsightGenerator(fallback=RuleBasedInsightGenerator(), client=fake)

    insights = await gen.refresh(db, user.id, period="monthly", reference=date(2026, 6, 10))
    assert len(insights) == 1
    assert insights[0]["type"] == "tip"
    assert insights[0]["id"].startswith("llm_")
    assert "₹5,000" in insights[0]["description"]

    # generate() serves the cache without calling the LLM again.
    cached = await gen.generate(db, user.id, period="monthly", reference=date(2026, 6, 10))
    assert cached == insights
    assert fake.calls == 1


async def test_insights_fallback_on_error(db):
    user = await _user(db)
    fake = FakeLLM(fail=True)
    gen = LLMInsightGenerator(fallback=RuleBasedInsightGenerator(), client=fake)

    result = await gen.refresh(db, user.id, period="monthly", reference=date(2026, 6, 10))
    assert isinstance(result, list)  # rule-based fallback, no exception

    # Nothing cached -> generate also serves the rule-based fallback.
    again = await gen.generate(db, user.id, period="monthly", reference=date(2026, 6, 10))
    assert isinstance(again, list)
