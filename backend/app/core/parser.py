"""Multi-format document parsing without OCR."""

from __future__ import annotations

import io
import logging
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pdfplumber
from docx import Document

from app.utils.config import get_settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
PAGE_NUMBER_RE = re.compile(
    r"(?im)^\s*(page\s+\d+(\s+of\s+\d+)?|\d+\s*/\s*\d+)\s*$"
)
WHITESPACE_RE = re.compile(r"[ \t]+")
MULTI_NEWLINE_RE = re.compile(r"\n{3,}")


class DocumentParser:
    """Parse uploaded bytes into cleaned plain text."""

    def parse(self, file_bytes: bytes, filename: str) -> str:
        """Parse file bytes; raise ValueError on validation/parse failure."""
        self._validate(file_bytes, filename)
        suffix = Path(filename).suffix.lower()

        if suffix == ".docx":
            text = self._parse_docx(file_bytes)
        elif suffix == ".pdf":
            text = self._parse_pdf(file_bytes)
        elif suffix == ".txt":
            text = file_bytes.decode("utf-8", errors="replace")
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        cleaned = self._post_process(text)
        if len(cleaned.strip()) < 20:
            raise ValueError(
                "No extractable text found. Scanned PDFs are not supported yet."
            )
        return cleaned

    def _validate(self, file_bytes: bytes, filename: str) -> None:
        settings = get_settings()
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {suffix}. Allowed: pdf, docx, txt"
            )
        if len(file_bytes) > settings.max_file_size_bytes:
            raise ValueError(
                f"File exceeds {settings.max_file_size_mb}MB limit"
            )
        if not file_bytes:
            raise ValueError("Empty file")

    def _parse_docx(self, file_bytes: bytes) -> str:
        document = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in document.paragraphs if p.text.strip())

    def _parse_pdf(self, file_bytes: bytes) -> str:
        pages = self._pdfplumber_pages(file_bytes)
        if pages and self._avg_chars(pages) >= 50:
            return self._join_pages(pages)

        logger.info("pdfplumber weak extract; trying PyMuPDF")
        pages = self._pymupdf_pages(file_bytes)
        if pages and self._avg_chars(pages) >= 20:
            return self._join_pages(pages)

        raise ValueError(
            "Could not extract text from PDF. OCR is not enabled in v1."
        )

    def _pdfplumber_pages(self, file_bytes: bytes) -> list[str]:
        pages: list[str] = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                pages.append(page.extract_text() or "")
        return pages

    def _pymupdf_pages(self, file_bytes: bytes) -> list[str]:
        import fitz

        pages: list[str] = []
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                pages.append(page.get_text("text") or "")
        return pages

    @staticmethod
    def _avg_chars(pages: list[str]) -> float:
        if not pages:
            return 0.0
        return sum(len(p.strip()) for p in pages) / len(pages)

    @staticmethod
    def _join_pages(pages: list[str]) -> str:
        return "\n\n".join(pages)

    def _post_process(self, text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        pages = [p for p in text.split("\n\n") if p.strip()]
        if len(pages) >= 3:
            text = self._strip_repeated_headers(pages)
        text = PAGE_NUMBER_RE.sub("", text)
        text = WHITESPACE_RE.sub(" ", text)
        text = MULTI_NEWLINE_RE.sub("\n\n", text)
        return text.strip()

    @staticmethod
    def _strip_repeated_headers(pages: list[str]) -> str:
        line_counts: Counter[str] = Counter()
        page_lines: list[list[str]] = []
        for page in pages:
            lines = [ln.strip() for ln in page.splitlines() if ln.strip()]
            page_lines.append(lines)
            for line in set(lines):
                if len(line) <= 80:
                    line_counts[line] += 1

        threshold = max(2, int(0.3 * len(pages)))
        repeated = {line for line, count in line_counts.items() if count >= threshold}

        cleaned_pages: list[str] = []
        for lines in page_lines:
            kept = [ln for ln in lines if ln not in repeated]
            cleaned_pages.append("\n".join(kept))
        return "\n\n".join(cleaned_pages)
