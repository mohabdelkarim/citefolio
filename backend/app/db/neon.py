"""Async Neon Postgres connection pool helpers."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional, Sequence
from uuid import UUID

import asyncpg

from app.utils.config import get_settings

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def init_pool() -> asyncpg.Pool:
    """Create the global asyncpg pool if missing."""
    global _pool
    if _pool is not None:
        return _pool

    settings = get_settings()
    # Prefer process env (Vercel) over cached settings; strip BOM/CRLF noise.
    dsn = (os.environ.get("DATABASE_URL") or settings.database_url or "")
    dsn = dsn.strip().lstrip("\ufeff").strip().strip('"').strip("'")
    if not dsn:
        raise RuntimeError("DATABASE_URL is empty")
    if not (dsn.startswith("postgres://") or dsn.startswith("postgresql://")):
        preview = dsn[:12].encode("unicode_escape").decode("ascii")
        raise RuntimeError(f"DATABASE_URL has invalid scheme ({preview})")

    _pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=1,
        max_size=5,
        command_timeout=60,
    )
    logger.info("Neon connection pool ready")
    return _pool


async def close_pool() -> None:
    """Close the global pool on shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Neon connection pool closed")


def get_pool() -> asyncpg.Pool:
    """Return the initialized pool or raise."""
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")
    return _pool


async def ensure_pool() -> asyncpg.Pool:
    """Initialize the pool on demand if startup failed or was skipped."""
    if _pool is None:
        return await init_pool()
    return _pool


@asynccontextmanager
async def get_connection(
    session_id: Optional[UUID] = None,
) -> AsyncIterator[asyncpg.Connection]:
    """Acquire a connection, optionally binding RLS session context."""
    pool = await ensure_pool()
    async with pool.acquire() as conn:
        if session_id is not None:
            async with conn.transaction():
                await conn.execute(
                    "SELECT set_config('app.session_id', $1, true)",
                    str(session_id),
                )
                yield conn
        else:
            yield conn


async def execute(
    query: str,
    *args: Any,
    session_id: Optional[UUID] = None,
) -> str:
    """Execute a statement and return the status tag."""
    async with get_connection(session_id=session_id) as conn:
        return await conn.execute(query, *args)


async def fetch(
    query: str,
    *args: Any,
    session_id: Optional[UUID] = None,
) -> list[asyncpg.Record]:
    """Fetch rows as a list of records."""
    async with get_connection(session_id=session_id) as conn:
        return await conn.fetch(query, *args)


async def fetchrow(
    query: str,
    *args: Any,
    session_id: Optional[UUID] = None,
) -> Optional[asyncpg.Record]:
    """Fetch a single row or None."""
    async with get_connection(session_id=session_id) as conn:
        return await conn.fetchrow(query, *args)


async def executemany(
    query: str,
    args: Sequence[Sequence[Any]],
    session_id: Optional[UUID] = None,
) -> None:
    """Execute many parameterized statements in one session-scoped txn."""
    async with get_connection(session_id=session_id) as conn:
        await conn.executemany(query, args)
