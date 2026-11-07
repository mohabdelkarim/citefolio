"""Cohere cross-encoder style reranking via managed API."""

from __future__ import annotations

import logging
from typing import Any, Optional

import cohere

from app.utils.config import get_settings

logger = logging.getLogger(__name__)
_reranker: Optional["CrossEncoderReranker"] = None


class CrossEncoderReranker:
    """Rerank retrieved chunks with Cohere Rerank."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.cohere_api_key:
            raise RuntimeError("COHERE_API_KEY is not configured")
        self._client = cohere.ClientV2(api_key=settings.cohere_api_key)
        self._model = settings.cohere_rerank_model

    def rerank(
        self,
        query: str,
        chunks: list[dict[str, Any]],
        top_n: int | None = None,
    ) -> list[dict[str, Any]]:
        if not chunks:
            return []
        settings = get_settings()
        top_n = top_n or settings.rerank_top_n
        documents = [c["text"] for c in chunks]
        response = self._client.rerank(
            model=self._model,
            query=query,
            documents=documents,
            top_n=min(top_n, len(documents)),
        )
        reranked: list[dict[str, Any]] = []
        for result in response.results:
            item = dict(chunks[result.index])
            item["rerank_score"] = float(result.relevance_score)
            item["score"] = float(result.relevance_score)
            reranked.append(item)
        logger.info("Reranked %s -> %s chunks", len(chunks), len(reranked))
        return reranked


def get_reranker() -> CrossEncoderReranker:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoderReranker()
    return _reranker
