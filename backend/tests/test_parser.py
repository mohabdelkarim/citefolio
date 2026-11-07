"""Unit tests for DocumentParser."""

from __future__ import annotations

import io

import pytest
from docx import Document

from app.core.parser import DocumentParser


def test_txt_parsing_returns_text() -> None:
    text = DocumentParser().parse(b"Hello Citefolio world from a text file.", "note.txt")
    assert "Citefolio" in text


def test_docx_parsing() -> None:
    buffer = io.BytesIO()
    doc = Document()
    doc.add_paragraph("Clause one about refunds and timelines.")
    doc.save(buffer)
    text = DocumentParser().parse(buffer.getvalue(), "policy.docx")
    assert "refunds" in text.lower()


def test_unsupported_type_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        DocumentParser().parse(b"abc", "image.png")


def test_empty_bytes_raise() -> None:
    with pytest.raises(ValueError, match="Empty"):
        DocumentParser().parse(b"", "empty.txt")
