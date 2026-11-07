"""Session create and destroy endpoints."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request

from app.db.neon import execute, fetchrow
from app.utils.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["session"])


def _hash_ip(ip: str | None) -> str | None:
    if not ip:
        return None
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()


@router.post("/session")
async def create_session(request: Request) -> dict:
    """Create an ephemeral session with TTL from config."""
    settings = get_settings()
    session_id = uuid4()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=settings.session_ttl_hours)
    client_ip = request.client.host if request.client else None

    await execute(
        """
        INSERT INTO user_sessions (session_id, created_at, expires_at, ip_hash)
        VALUES ($1, $2, $3, $4)
        """,
        session_id,
        now,
        expires_at,
        _hash_ip(client_ip),
    )
    return {
        "session_id": str(session_id),
        "expires_at": expires_at.isoformat(),
    }


@router.delete("/session/{session_id}")
async def delete_session(session_id: str) -> dict:
    """Delete session rows and cascaded document chunks."""
    try:
        sid = UUID(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid session_id") from exc

    count_row = await fetchrow(
        "SELECT COUNT(*)::int AS n FROM documents WHERE session_id = $1",
        sid,
        session_id=sid,
    )
    deleted_chunks = int(count_row["n"]) if count_row else 0

    await execute(
        "DELETE FROM user_sessions WHERE session_id = $1",
        sid,
    )
    logger.info("Deleted session %s (%s chunks)", sid, deleted_chunks)
    return {"deleted_chunks": deleted_chunks}
