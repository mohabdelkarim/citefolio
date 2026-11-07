"""Neon-backed semantic response cache."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional
from uuid import UUID

from app.core.vector_utils import to_pgvector_literal
from app.db.neon import execute, fetchrow
from app.utils.config import get_settings

logger = logging.getLogger(__name__)


class SemanticCache:
    """Cosine similarity cache stored in Postgres."""

    async def get(
        self,
        query_embedding: list[float],
        session_id: UUID,
    ) -> Optional[dict[str, Any]]:
        """Return cached response when similarity exceeds threshold."""
        settings = get_settings()
        row = await fetchrow(
            """
            SELECT id, response, sources,
                   1 - (query_embedding <=> $1::vector) AS similarity
            FROM semantic_cache
            WHERE session_id = $2
            ORDER BY query_embedding <=> $1::vector
            LIMIT 1
            """,
            to_pgvector_literal(query_embedding),
            session_id,
            session_id=session_id,
        )
        if row is None:
            return None
        if float(row["similarity"]) < settings.cache_similarity_threshold:
            return None

        await execute(
            "UPDATE semantic_cache SET hit_count = hit_count + 1 WHERE id = $1",
            row["id"],
            session_id=session_id,
        )
        sources = row["sources"]
        if isinstance(sources, str):
            sources = json.loads(sources)
        logger.info("Semantic cache hit id=%s", row["id"])
        return {"response": row["response"], "sources": sources}

    async def set(
        self,
        query_embedding: list[float],
        response: str,
        sources: list[dict[str, Any]],
        session_id: UUID,
        query_text: str = "",
    ) -> None:
        """Persist a new cache entry for the session."""
        await execute(
            """
            INSERT INTO semantic_cache
                (session_id, query_embedding, query_text, response, sources)
            VALUES ($1, $2::vector, $3, $4, $5::jsonb)
            """,
            session_id,
            to_pgvector_literal(query_embedding),
            query_text,
            response,
            json.dumps(sources),
            session_id=session_id,
        )
