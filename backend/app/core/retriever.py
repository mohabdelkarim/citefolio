"""Hybrid BM25 + pgvector retrieval with RRF fusion."""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from uuid import UUID

from rank_bm25 import BM25Okapi

from app.core.vector_utils import to_pgvector_literal
from app.db.neon import fetch
from app.utils.config import get_settings

logger = logging.getLogger(__name__)
TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


class HybridRetriever:
    """Retrieve session-scoped chunks via semantic + keyword fusion."""

    async def retrieve(
        self,
        query: str,
        query_embedding: list[float],
        session_id: UUID,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        settings = get_settings()
        top_k = top_k or settings.retrieval_top_k
        semantic = await self._semantic_search(
            query_embedding, session_id, top_k
        )
        bm25 = await self._bm25_search(query, session_id, top_k)
        fused = self._rrf_fuse(semantic, bm25, settings.rrf_k)
        return fused[:top_k]

    async def _semantic_search(
        self,
        query_embedding: list[float],
        session_id: UUID,
        top_k: int,
    ) -> list[dict[str, Any]]:
        rows = await fetch(
            """
            SELECT id, chunk_text, metadata,
                   1 - (embedding <=> $1::vector) AS similarity
            FROM documents
            WHERE session_id = $2
            ORDER BY embedding <=> $1::vector
            LIMIT $3
            """,
            to_pgvector_literal(query_embedding),
            session_id,
            top_k,
            session_id=session_id,
        )
        return [self._row_to_chunk(row, float(row["similarity"])) for row in rows]

    async def _bm25_search(
        self,
        query: str,
        session_id: UUID,
        top_k: int,
    ) -> list[dict[str, Any]]:
        rows = await fetch(
            """
            SELECT id, chunk_text, metadata
            FROM documents
            WHERE session_id = $1
            """,
            session_id,
            session_id=session_id,
        )
        if not rows:
            return []

        corpus_tokens = [self._tokenize(row["chunk_text"]) for row in rows]
        if not any(corpus_tokens):
            return []
        bm25 = BM25Okapi(corpus_tokens)
        scores = bm25.get_scores(self._tokenize(query))
        ranked = sorted(
            enumerate(scores),
            key=lambda item: item[1],
            reverse=True,
        )[:top_k]
        results: list[dict[str, Any]] = []
        for idx, score in ranked:
            if score <= 0:
                continue
            results.append(self._row_to_chunk(rows[idx], float(score)))
        return results

    def _rrf_fuse(
        self,
        semantic: list[dict[str, Any]],
        bm25: list[dict[str, Any]],
        k: int,
    ) -> list[dict[str, Any]]:
        scores: dict[Any, float] = {}
        payload: dict[Any, dict[str, Any]] = {}

        for rank, chunk in enumerate(semantic, start=1):
            doc_id = chunk["id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
            payload[doc_id] = chunk

        for rank, chunk in enumerate(bm25, start=1):
            doc_id = chunk["id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
            payload[doc_id] = chunk

        ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        fused: list[dict[str, Any]] = []
        for doc_id, rrf_score in ordered:
            item = dict(payload[doc_id])
            item["rrf_score"] = rrf_score
            # Keep original similarity for guardrails; expose RRF separately.
            item["score"] = float(item.get("similarity", rrf_score))
            fused.append(item)
        return fused

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [t.lower() for t in TOKEN_RE.findall(text or "")]

    @staticmethod
    def _row_to_chunk(row: Any, score: float) -> dict[str, Any]:
        metadata = row["metadata"]
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        return {
            "id": row["id"],
            "text": row["chunk_text"],
            "metadata": metadata or {},
            "similarity": score,
            "score": score,
        }
