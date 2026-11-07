"""Recursive token-aware document chunking."""

from __future__ import annotations

from typing import Any

import tiktoken

from app.utils.config import get_settings

SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


class DocumentChunker:
    """Split text into overlapping chunks with source metadata."""

    def __init__(self) -> None:
        settings = get_settings()
        self.chunk_size = settings.chunk_size
        self.overlap = settings.chunk_overlap_tokens
        self._enc = tiktoken.get_encoding("cl100k_base")

    def chunk(self, text: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """Return chunk dicts with positional and source metadata."""
        filename = str(metadata.get("filename", "document"))
        parts = self._split_text(text)
        if not parts:
            return []

        total = len(parts)
        chars_per_page = 3000
        chunks: list[dict[str, Any]] = []
        search_from = 0

        for index, part in enumerate(parts):
            start = text.find(part, search_from)
            if start < 0:
                start = search_from
            end = start + len(part)
            search_from = max(start + 1, end - self.overlap)
            chunks.append(
                {
                    "text": part,
                    "char_start": start,
                    "char_end": end,
                    "chunk_index": index,
                    "total_chunks": total,
                    "filename": filename,
                    "estimated_page": max(1, start // chars_per_page + 1),
                    "word_count": len(part.split()),
                }
            )
        return chunks

    def _token_len(self, text: str) -> int:
        return len(self._enc.encode(text))

    def _split_text(self, text: str) -> list[str]:
        text = text.strip()
        if not text:
            return []
        if self._token_len(text) <= self.chunk_size:
            return [text]
        return self._recursive_split(text, SEPARATORS)

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        sep = separators[0]
        rest = separators[1:] or [""]

        pieces = text.split(sep) if sep else list(text)
        merged: list[str] = []
        current = ""

        for piece in pieces:
            candidate = piece if not current else f"{current}{sep}{piece}"
            if self._token_len(candidate) <= self.chunk_size:
                current = candidate
                continue
            if current:
                merged.append(current)
            if self._token_len(piece) > self.chunk_size and rest:
                merged.extend(self._recursive_split(piece, rest))
                current = ""
            else:
                current = piece

        if current:
            merged.append(current)

        return self._apply_overlap(merged)

    def _apply_overlap(self, chunks: list[str]) -> list[str]:
        if len(chunks) <= 1 or self.overlap <= 0:
            return chunks

        result: list[str] = [chunks[0]]
        for chunk in chunks[1:]:
            prev_tokens = self._enc.encode(result[-1])
            overlap_tokens = prev_tokens[-self.overlap :]
            prefix = self._enc.decode(overlap_tokens)
            combined = f"{prefix}{chunk}" if prefix else chunk
            if self._token_len(combined) > self.chunk_size * 2:
                result.append(chunk)
            else:
                result.append(combined)
        return result
