"""Document upload endpoint: parse, chunk, embed, store."""

from __future__ import annotations

import gc
import json
import logging
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.chunker import DocumentChunker
from app.core.embedder import get_embedder
from app.core.parser import ALLOWED_EXTENSIONS, DocumentParser
from app.core.vector_utils import to_pgvector_literal
from app.db.neon import executemany
from app.db.sessions import is_active_session
from app.utils.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_document(
    session_id: str = Form(...),
    file: UploadFile = File(...),
) -> dict:
    """Process an uploaded file entirely in memory and store embeddings."""
    settings = get_settings()
    filename = file.filename or "document.txt"
    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type: {suffix}",
        )

    try:
        sid = UUID(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid session_id") from exc

    if not await is_active_session(sid):
        raise HTTPException(status_code=404, detail="Session expired or missing")

    file_bytes = await file.read()
    try:
        if len(file_bytes) > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max {settings.max_file_size_mb}MB",
            )

        try:
            text = DocumentParser().parse(file_bytes, filename)
        except ValueError as exc:
            message = str(exc)
            if "exceeds" in message.lower():
                raise HTTPException(status_code=413, detail=message) from exc
            raise HTTPException(status_code=422, detail=message) from exc

        chunks = DocumentChunker().chunk(text, {"filename": filename})
        if not chunks:
            raise HTTPException(status_code=422, detail="No chunks produced")

        try:
            embeddings = get_embedder().embed_chunks([c["text"] for c in chunks])
        except Exception as exc:
            logger.exception("Embedding failed")
            raise HTTPException(
                status_code=500,
                detail="Failed to embed document",
            ) from exc

        insert_sql = """
            INSERT INTO documents (session_id, chunk_text, embedding, metadata)
            VALUES ($1, $2, $3::vector, $4::jsonb)
        """
        rows = [
            (
                sid,
                chunk["text"],
                to_pgvector_literal(embedding),
                json.dumps(chunk),
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]
        try:
            await executemany(insert_sql, rows, session_id=sid)
        except Exception as exc:
            logger.exception("Failed to store chunks")
            raise HTTPException(
                status_code=500,
                detail="Failed to store document",
            ) from exc

        estimated_pages = max(c["estimated_page"] for c in chunks)
        return {
            "status": "ready",
            "session_id": str(sid),
            "chunks_created": len(chunks),
            "filename": filename,
            "estimated_pages": estimated_pages,
        }
    finally:
        del file_bytes
        gc.collect()
