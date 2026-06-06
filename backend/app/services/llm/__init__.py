"""LLM client factory.

Returns a configured provider client, or ``None`` when no API key is set — in
which case the AI services fall back to their rule-based implementations.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from app.core.config import settings
from app.services.llm.anthropic_client import AnthropicClient
from app.services.llm.base import LLMClient, LLMError

logger = logging.getLogger("ledgeriq.ai")

__all__ = ["LLMClient", "LLMError", "get_llm_client"]


@lru_cache
def get_llm_client() -> LLMClient | None:
    if not settings.LLM_API_KEY:
        return None
    provider = (settings.LLM_PROVIDER or "").strip().lower()
    if provider == "anthropic":
        return AnthropicClient(
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
    logger.warning(
        "Unknown LLM_PROVIDER %r — AI features will use rule-based fallbacks", provider
    )
    return None
