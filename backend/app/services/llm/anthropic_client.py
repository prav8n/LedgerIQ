"""Anthropic (Claude) provider for the LLM client interface."""

from __future__ import annotations

import httpx

from app.services.llm.base import LLMClient, LLMError

_API_URL = "https://api.anthropic.com/v1/messages"
_API_VERSION = "2023-06-01"


class AnthropicClient(LLMClient):
    def __init__(self, *, api_key: str, model: str, timeout: float = 20.0) -> None:
        self._api_key = api_key
        self.model = model
        self._timeout = timeout

    async def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": _API_VERSION,
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(_API_URL, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:  # transport / bad JSON
            raise LLMError(f"Anthropic request failed: {exc}") from exc

        parts = data.get("content", []) if isinstance(data, dict) else []
        text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
        if not text.strip():
            raise LLMError("Empty LLM response")
        return text
