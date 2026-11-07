"""Session existence and TTL checks."""

from __future__ import annotations

from uuid import UUID

from app.db.neon import fetchrow


async def is_active_session(session_id: UUID) -> bool:
    """Return True when the session exists and has not expired."""
    row = await fetchrow(
        """
        SELECT 1 AS ok
        FROM user_sessions
        WHERE session_id = $1
          AND expires_at > NOW()
        """,
        session_id,
    )
    return row is not None
