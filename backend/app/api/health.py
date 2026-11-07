"""Dependency health checks for monitoring and Vercel."""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter

from app.db.neon import ensure_pool, fetchrow
from app.utils.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["health"])


async def _check_db() -> str:
    try:
        await ensure_pool()
        row = await fetchrow("SELECT 1 AS ok")
        return "connected" if row and row["ok"] == 1 else "error"
    except Exception:
        logger.exception("Health DB check failed")
        return "error"


async def _ping(url: str, api_key: str) -> str:
    if not api_key:
        return "unavailable"
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.get(
                f"{url.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            return "available" if response.status_code < 500 else "unavailable"
    except Exception:
        return "unavailable"


@router.get("/health")
async def health() -> dict:
    """Return status of DB and configured providers."""
    settings = get_settings()
    db_status = await _check_db()
    groq = await _ping(settings.groq_base_url, settings.groq_api_key)
    cerebras = await _ping(settings.cerebras_base_url, settings.cerebras_api_key)

    if settings.voyage_api_key:
        embedder = "configured"
    elif settings.mistral_api_key:
        embedder = "configured_mistral"
    else:
        embedder = "missing_key"
    reranker = (
        "configured"
        if settings.cohere_api_key
        else "skipped_no_cohere"
    )

    status = "ok" if db_status == "connected" else "degraded"
    return {
        "status": status,
        "db": db_status,
        "embedder": embedder,
        "reranker": reranker,
        "groq": groq,
        "cerebras": cerebras,
    }
