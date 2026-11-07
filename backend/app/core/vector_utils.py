"""Helpers for pgvector literals with asyncpg."""

from __future__ import annotations


def to_pgvector_literal(values: list[float]) -> str:
    """Format a float list as a pgvector input literal."""
    return "[" + ",".join(f"{v:.8f}" for v in values) + "]"
