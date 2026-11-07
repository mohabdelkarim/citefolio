"""Unit tests for hybrid fusion helpers."""

from __future__ import annotations

from app.core.retriever import HybridRetriever


def test_rrf_deduplicates_and_ranks() -> None:
    semantic = [
        {"id": 1, "text": "alpha", "metadata": {}, "score": 0.9},
        {"id": 2, "text": "beta", "metadata": {}, "score": 0.8},
    ]
    bm25 = [
        {"id": 2, "text": "beta", "metadata": {}, "score": 5.0},
        {"id": 3, "text": "gamma keyword", "metadata": {}, "score": 4.0},
    ]
    fused = HybridRetriever()._rrf_fuse(semantic, bm25, k=60)
    ids = [item["id"] for item in fused]
    assert ids.count(2) == 1
    assert set(ids) == {1, 2, 3}
    assert fused[0]["rrf_score"] >= fused[-1]["rrf_score"]


def test_tokenize_keeps_words() -> None:
    tokens = HybridRetriever._tokenize("Refund window vs διαφορά policy")
    assert "refund" in tokens
    assert "διαφορά" in tokens
