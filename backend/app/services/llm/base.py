"""Provider-agnostic LLM client interface."""

from __future__ import annotations

import abc


class LLMError(Exception):
    """Raised for any LLM provider/transport failure."""


class LLMClient(abc.ABC):
    """Minimal text-completion interface implemented by each provider."""

    model: str

    @abc.abstractmethod
    async def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        """Return the model's text response, or raise :class:`LLMError`."""
