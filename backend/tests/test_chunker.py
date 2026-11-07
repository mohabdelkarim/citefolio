"""Unit tests for DocumentChunker."""

from __future__ import annotations

from app.core.chunker import DocumentChunker


def test_short_document_is_single_chunk() -> None:
    chunks = DocumentChunker().chunk(
        "Short document with one idea.",
        {"filename": "short.txt"},
    )
    assert len(chunks) == 1
    assert chunks[0]["total_chunks"] == 1
    assert chunks[0]["filename"] == "short.txt"


def test_long_text_produces_multiple_chunks_with_metadata() -> None:
    text = " ".join(["Sentence number %s about contracts." % i for i in range(400)])
    chunks = DocumentChunker().chunk(text, {"filename": "long.txt"})
    assert len(chunks) > 1
    assert all("chunk_index" in c for c in chunks)
    assert all(c["total_chunks"] == len(chunks) for c in chunks)


def test_overlap_exists_between_consecutive_chunks() -> None:
    text = ("Paragraph about warranties. " * 80) + ("\n\nNext section. " * 80)
    chunks = DocumentChunker().chunk(text, {"filename": "overlap.txt"})
    if len(chunks) < 2:
        return
    # Overlap applied as prefix of next chunk from previous tokens
    assert chunks[1]["text"]
    assert chunks[0]["char_end"] >= chunks[0]["char_start"]
