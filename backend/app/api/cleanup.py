"""Scheduled cleanup endpoint for Vercel Cron.

Document rows use FORCE ROW LEVEL SECURITY, so bare DELETE FROM documents
without app.session_id only matches the nil UUID. Cleanup therefore deletes
expired (or age-capped) sessions and relies on FK CASCADE for chunks/cache.
"""

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
    mode: str = Query("all"),
    authorization: str | None = Header(default=None),
) -> dict:
    """Run TTL cleanup. Requires Bearer CRON_SECRET."""
    settings = get_settings()
    if not settings.cron_secret or settings.cron_secret == "change_me":
        raise HTTPException(status_code=503, detail="CRON_SECRET not configured")
    expected = f"Bearer {settings.cron_secret}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    ttl_hours = max(1, int(settings.session_ttl_hours))
    deleted = {"sessions": 0, "cache": 0}

    if mode in {"hourly", "all"}:
        result = await execute(
            "DELETE FROM user_sessions WHERE expires_at < NOW()"
        )
        deleted["sessions"] += _parse_delete_count(result)

    if mode in {"daily", "all"}:
        # Safety net for sessions whose expires_at was never hit (clock skew, etc.)
        result = await execute(
            """
            DELETE FROM user_sessions
            WHERE created_at < NOW() - make_interval(hours => $1)
            """,
            ttl_hours * 12,
        )
        deleted["sessions"] += _parse_delete_count(result)

    if mode in {"weekly", "all"}:
        # Owner role bypasses RLS when FORCE is not set on semantic_cache.
        result = await execute(
            "DELETE FROM semantic_cache WHERE created_at < NOW() - INTERVAL '7 days'"
        )
        deleted["cache"] += _parse_delete_count(result)

    logger.info("Cleanup mode=%s deleted=%s", mode, deleted)
    return {"status": "ok", "mode": mode, "deleted": deleted, "ttl_hours": ttl_hours}


def _parse_delete_count(status: str) -> int:
    # asyncpg returns e.g. "DELETE 3"
    parts = status.split()
    if len(parts) == 2 and parts[1].isdigit():
        return int(parts[1])
    return 0
