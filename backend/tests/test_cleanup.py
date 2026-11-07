"""Unit tests for cleanup helpers."""

from __future__ import annotations

from app.api.cleanup import _parse_delete_count


def test_parse_delete_count() -> None:
    assert _parse_delete_count("DELETE 3") == 3
    assert _parse_delete_count("DELETE 0") == 0
    assert _parse_delete_count("OK") == 0
