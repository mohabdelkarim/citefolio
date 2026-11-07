"""RAG query pipeline orchestration (API stays thin)."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, AsyncIterator
from uuid import UUID

from app.core.cache import SemanticCache
from app.core.embedder import get_embedder
from app.core.generator import RAGGenerator
from app.core.guardrails import InputGuardrail, OutputGuardrail, RetrievalGuardrail
from app.core.query_transform import QueryTransformer
from app.core.reranker import get_reranker
from app.core.retriever import HybridRetriever
from app.db.neon import execute
from app.utils.config import get_settings

logger = logging.getLogger(__name__)

NO_INFO = (
    "I don't have enough information to answer this based on the provided documents."
)


def sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_rag_answer(
    session_id: UUID,
    query: str,
) -> AsyncIterator[str]:
    """Run cache → retrieve → rerank → generate and yield SSE frames."""
    started = time.perf_counter()
    provider_used = "none"
    full_text = ""
    sources: list[dict[str, Any]] = []
    context_texts: list[str] = []
    query_embedding: list[float] = []

    try:
        embedder = get_embedder()
        query_embedding = embedder.embed_query(query)
        cache = SemanticCache()
        cached = await cache.get(query_embedding, session_id)
        if cached:
            text = cached["response"]
            sources = cached["sources"]
            for token in text:
                yield sse("token", {"content": token})
            yield sse("sources", {"sources": sources})
            yield sse("done", {"provider": "cache", "cached": True})
            return

        transformer = QueryTransformer()
        retriever = HybridRetriever()
        chunks: list[dict[str, Any]] = []

        if transformer.should_decompose(query):
            subqueries = await transformer.decompose(query) or [query]
            for sub in subqueries:
                sub_emb = embedder.embed_query(sub)
                part = await retriever.retrieve(sub, sub_emb, session_id)
                chunks.extend(part)
        else:
            hyde_text = await transformer.hyde(query)
            retrieval_query = hyde_text or await transformer.rewrite(query) or query
            retrieval_emb = (
                embedder.embed_query(retrieval_query)
                if retrieval_query != query
                else query_embedding
            )
            chunks = await retriever.retrieve(
                query,
                retrieval_emb,
                session_id,
            )

        seen: set[Any] = set()
        unique: list[dict[str, Any]] = []
        for chunk in chunks:
            if chunk["id"] in seen:
                continue
            seen.add(chunk["id"])
            unique.append(chunk)
        chunks = unique

        relevant, max_score = RetrievalGuardrail().check(chunks)
        if not relevant:
            yield sse("token", {"content": NO_INFO})
            yield sse("sources", {"sources": []})
            yield sse(
                "done",
                {"provider": "none", "cached": False, "max_score": max_score},
            )
            return

        try:
            reranked = get_reranker().rerank(query, chunks[:20])
        except Exception:
            logger.exception("Rerank failed; using RRF order")
            reranked = chunks[: get_settings().rerank_top_n]

        generator = RAGGenerator()
        context = generator.build_context(reranked)
        context_texts = [c["text"] for c in reranked]
        sources = generator.extract_sources(reranked)

        async for token, provider in generator.generate(query, context):
            provider_used = provider
            full_text += token
            yield sse("token", {"content": token})

        if not OutputGuardrail().check(full_text, context_texts):
            logger.warning("Output guardrail flagged response")

        await cache.set(
            query_embedding,
            full_text,
            sources,
            session_id,
            query_text=query,
        )

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        await execute(
            """
            INSERT INTO query_logs
                (session_id, query_text, response_text, provider_used, response_time_ms)
            VALUES ($1, $2, $3, $4, $5)
            """,
            session_id,
            query,
            full_text,
            provider_used,
            elapsed_ms,
            session_id=session_id,
        )

        yield sse("sources", {"sources": sources})
        yield sse(
            "done",
            {
                "provider": provider_used,
                "cached": False,
                "response_time_ms": elapsed_ms,
            },
        )
    except Exception:
        logger.exception("Query pipeline failed")
        yield sse("error", {"detail": "Query failed"})
