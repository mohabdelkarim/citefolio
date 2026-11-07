"""HyDE, rewrite, and comparison-query decomposition."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import AsyncOpenAI

from app.utils.config import get_settings

logger = logging.getLogger(__name__)

COMPARE_WORDS = [
    "compare",
    "difference",
    "vs",
    "versus",
    "contrast",
    "between",
    "both",
    "συγκρίνε",
    "διαφορά",
    "μεταξύ",
]


class QueryTransformer:
    """LLM-assisted query rewriting for retrieval quality."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(
            api_key=settings.groq_api_key or "missing",
            base_url=settings.groq_base_url,
        )
        self._model = settings.groq_model

    def should_decompose(self, query: str) -> bool:
        lowered = query.lower()
        return any(word in lowered for word in COMPARE_WORDS)

    async def decompose(self, query: str) -> list[str]:
        prompt = (
            "Split this question into simpler sub-questions for document "
            "retrieval. Return ONLY a JSON array of strings. Max 3 questions.\n\n"
            f"Question: {query}"
        )
        raw = await self._complete(prompt, max_tokens=256)
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(item) for item in parsed][:3]
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, list):
                        return [str(item) for item in parsed][:3]
                except json.JSONDecodeError:
                    pass
        return [query]

    async def rewrite(self, query: str) -> str:
        prompt = (
            "Rewrite the question to be more retrieval-friendly. "
            "Expand abbreviations. Keep under 150 characters. "
            "Return only the rewritten question.\n\n"
            f"Question: {query}"
        )
        rewritten = (await self._complete(prompt, max_tokens=120)).strip()
        return rewritten[:150] if rewritten else query

    async def hyde(self, query: str) -> str:
        prompt = (
            "Write a short hypothetical answer paragraph to this question "
            "as if quoting a document. No preamble.\n\n"
            f"Question: {query}"
        )
        return (await self._complete(prompt, max_tokens=220)).strip() or query

    async def _complete(self, prompt: str, max_tokens: int) -> str:
        settings = get_settings()
        if not settings.groq_api_key:
            logger.warning("GROQ_API_KEY missing; skipping query transform")
            return ""
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                temperature=0,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""
        except Exception:
            logger.exception("Query transform LLM call failed")
            return ""
