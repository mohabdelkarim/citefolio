"""Streaming RAG generation with Groq primary and Cerebras fallback."""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from app.utils.config import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a precise document assistant.
Answer ONLY based on the provided context.
Rules:
- If the answer is not in the context, respond:
  "I don't have enough information to answer this based on the provided documents."
- Always cite the source filename and page
- Be concise and direct
- Do not add information from outside the context
- Use the same language as the user's question
"""


class RAGGenerator:
    """Build ordered context and stream an LLM answer."""

    def build_context(self, chunks: list[dict[str, Any]]) -> str:
        ordered = self._anti_lost_in_middle(chunks)
        blocks: list[str] = []
        for chunk in ordered:
            meta = chunk.get("metadata") or {}
            filename = meta.get("filename", "document")
            page = meta.get("estimated_page", "?")
            blocks.append(f"[Source: {filename}, p.{page}]\n{chunk['text']}")
        return "\n\n".join(blocks)

    def build_prompt(self, query: str, context: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}",
            },
        ]

    async def generate(
        self,
        query: str,
        context: str,
    ) -> AsyncIterator[tuple[str, str]]:
        """Yield (token, provider) pairs from Groq or Cerebras."""
        settings = get_settings()
        messages = self.build_prompt(query, context)
        providers = [
            ("groq", settings.groq_api_key, settings.groq_base_url, settings.groq_model),
            (
                "cerebras",
                settings.cerebras_api_key,
                settings.cerebras_base_url,
                settings.cerebras_model,
            ),
        ]

        last_error: Exception | None = None
        for name, api_key, base_url, model in providers:
            if not api_key:
                continue
            try:
                client = AsyncOpenAI(api_key=api_key, base_url=base_url)
                stream = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=settings.llm_temperature,
                    max_tokens=settings.llm_max_tokens,
                    stream=True,
                )
                logger.info("Generating with provider=%s model=%s", name, model)
                async for event in stream:
                    delta = event.choices[0].delta.content or ""
                    if delta:
                        yield delta, name
                return
            except Exception as exc:
                last_error = exc
                logger.exception("Provider %s failed; trying fallback", name)

        raise RuntimeError(f"All LLM providers failed: {last_error}")

    @staticmethod
    def _anti_lost_in_middle(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ranked = sorted(
            chunks,
            key=lambda c: float(c.get("rerank_score", c.get("score", 0.0))),
            reverse=True,
        )
        if len(ranked) <= 2:
            return ranked
        first = ranked[0]
        last = ranked[1]
        middle = ranked[2:]
        return [first, *middle, last]

    @staticmethod
    def extract_sources(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        sources: list[dict[str, Any]] = []
        seen: set[str] = set()
        for chunk in chunks:
            meta = chunk.get("metadata") or {}
            filename = str(meta.get("filename", "document"))
            page = meta.get("estimated_page", "?")
            key = f"{filename}:{page}"
            if key in seen:
                continue
            seen.add(key)
            sources.append(
                {
                    "filename": filename,
                    "page": page,
                    "snippet": chunk["text"][:240],
                }
            )
        return sources
