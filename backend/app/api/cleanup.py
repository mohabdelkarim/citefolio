"""Scheduled cleanup endpoint for Vercel Cron."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException, Query

from app.db.neon import execute
from app.utils.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["cleanup"])


@router.get("/cleanup")
@router.post("/cleanup")
async def cleanup(
    mode: str = Query("hourly"),
    authorization: str | None = Header(default=None),
) -> dict:
    """Run TTL cleanup. Requires Bearer CRON_SECRET."""
    settings = get_settings()
    expected = f"Bearer {settings.cron_secret}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    deleted = {"documents": 0, "sessions": 0, "cache": 0}

    if mode in {"hourly", "all"}:
        result = await execute(
            "DELETE FROM documents WHERE created_at < NOW() - INTERVAL '2 hours'"
        )
        deleted["documents"] += _parse_delete_count(result)
        result = await execute("DELETE FROM user_sessions WHERE expires_at < NOW()")
        deleted["sessions"] += _parse_delete_count(result)

    if mode in {"daily", "all"}:
        result = await execute(
            "DELETE FROM documents WHERE created_at < NOW() - INTERVAL '24 hours'"
        )
        deleted["documents"] += _parse_delete_count(result)

    if mode in {"weekly", "all"}:
        result = await execute(
            "DELETE FROM semantic_cache WHERE created_at < NOW() - INTERVAL '7 days'"
        )
        deleted["cache"] += _parse_delete_count(result)

    logger.info("Cleanup mode=%s deleted=%s", mode, deleted)
    return {"status": "ok", "mode": mode, "deleted": deleted}


def _parse_delete_count(status: str) -> int:
    # asyncpg returns e.g. "DELETE 3"
    parts = status.split()
    if len(parts) == 2 and parts[1].isdigit():
        return int(parts[1])
    return 0
