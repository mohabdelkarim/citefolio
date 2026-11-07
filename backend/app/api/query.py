"""Query pipeline endpoint with streaming responses."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, AsyncIterator
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

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
router = APIRouter(prefix="/api", tags=["query"])

NO_INFO = (
    "I don't have enough information to answer this based on the provided documents."
)


class QueryRequest(BaseModel):
    session_id: str
    query: str = Field(..., min_length=1, max_length=1000)


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/query")
async def query_documents(body: QueryRequest) -> StreamingResponse:
    """Run the full RAG pipeline and stream tokens as SSE."""
    try:
        session_id = UUID(body.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid session_id") from exc

    ok, reason = InputGuardrail().check(body.query)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)

    async def event_stream() -> AsyncIterator[str]:
        started = time.perf_counter()
        provider_used = "none"
        full_text = ""
        sources: list[dict[str, Any]] = []
        context_texts: list[str] = []
        query_embedding: list[float] = []

        try:
            embedder = get_embedder()
            query_embedding = embedder.embed_query(body.query)
            cache = SemanticCache()
            cached = await cache.get(query_embedding, session_id)
            if cached:
                text = cached["response"]
                sources = cached["sources"]
                for token in text:
                    yield _sse("token", {"content": token})
                yield _sse("sources", {"sources": sources})
                yield _sse("done", {"provider": "cache", "cached": True})
                return

            transformer = QueryTransformer()
            retriever = HybridRetriever()
            chunks: list[dict[str, Any]] = []

            if transformer.should_decompose(body.query):
                subqueries = await transformer.decompose(body.query) or [body.query]
                for sub in subqueries:
                    sub_emb = embedder.embed_query(sub)
                    part = await retriever.retrieve(sub, sub_emb, session_id)
                    chunks.extend(part)
            else:
                hyde_text = await transformer.hyde(body.query)
                retrieval_query = hyde_text or await transformer.rewrite(body.query) or body.query
                retrieval_emb = (
                    embedder.embed_query(retrieval_query)
                    if retrieval_query != body.query
                    else query_embedding
                )
                chunks = await retriever.retrieve(
                    body.query,
                    retrieval_emb,
                    session_id,
                )

            # Deduplicate by id preserving order
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
                yield _sse("token", {"content": NO_INFO})
                yield _sse("sources", {"sources": []})
                yield _sse(
                    "done",
                    {"provider": "none", "cached": False, "max_score": max_score},
                )
                return

            try:
                reranked = get_reranker().rerank(body.query, chunks[:20])
            except Exception:
                logger.exception("Rerank failed; using RRF order")
                reranked = chunks[: get_settings().rerank_top_n]

            generator = RAGGenerator()
            context = generator.build_context(reranked)
            context_texts = [c["text"] for c in reranked]
            sources = generator.extract_sources(reranked)

            async for token, provider in generator.generate(body.query, context):
                provider_used = provider
                full_text += token
                yield _sse("token", {"content": token})

            if not OutputGuardrail().check(full_text, context_texts):
                logger.warning("Output guardrail flagged response")

            await cache.set(
                query_embedding,
                full_text,
                sources,
                session_id,
                query_text=body.query,
            )

            elapsed_ms = int((time.perf_counter() - started) * 1000)
            await execute(
                """
                INSERT INTO query_logs
                    (session_id, query_text, response_text, provider_used, response_time_ms)
                VALUES ($1, $2, $3, $4, $5)
                """,
                session_id,
                body.query,
                full_text,
                provider_used,
                elapsed_ms,
                session_id=session_id,
            )

            yield _sse("sources", {"sources": sources})
            yield _sse(
                "done",
                {
                    "provider": provider_used,
                    "cached": False,
                    "response_time_ms": elapsed_ms,
                },
            )
        except Exception:
            logger.exception("Query pipeline failed")
            yield _sse("error", {"detail": "Query failed"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
