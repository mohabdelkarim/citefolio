"""User feedback collection for evaluation."""

from __future__ import annotations

from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db.neon import execute

router = APIRouter(prefix="/api", tags=["feedback"])


class FeedbackRequest(BaseModel):
    session_id: str
    query_id: Optional[int] = None
    rating: Literal[-1, 1]
    comment: Optional[str] = Field(default=None, max_length=2000)


@router.post("/feedback")
async def submit_feedback(body: FeedbackRequest) -> dict:
    """Store thumbs up/down feedback for a query."""
    try:
        sid = UUID(body.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid session_id") from exc

    await execute(
        """
        INSERT INTO query_feedback (session_id, query_id, rating, comment)
        VALUES ($1, $2, $3, $4)
        """,
        sid,
        body.query_id,
        body.rating,
        body.comment,
        session_id=sid,
    )
    return {"status": "stored"}
