"""Query endpoint: validate input, stream RAG SSE."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.guardrails import InputGuardrail
from app.core.pipeline import stream_rag_answer
from app.db.sessions import is_active_session

router = APIRouter(prefix="/api", tags=["query"])


class QueryRequest(BaseModel):
    session_id: str
    query: str = Field(..., min_length=1, max_length=1000)


@router.post("/query")
async def query_documents(body: QueryRequest) -> StreamingResponse:
    """Run the full RAG pipeline and stream tokens as SSE."""
    try:
        session_id = UUID(body.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid session_id") from exc

    if not await is_active_session(session_id):
        raise HTTPException(status_code=404, detail="Session expired or missing")

    ok, reason = InputGuardrail().check(body.query)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)

    return StreamingResponse(
        stream_rag_answer(session_id, body.query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
