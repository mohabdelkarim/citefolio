"""Citefolio FastAPI entrypoint for Vercel and local uvicorn."""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import cleanup as cleanup_api
from app.api import feedback as feedback_api
from app.api import health as health_api
from app.api import query as query_api
from app.api import session as session_api
from app.api import upload as upload_api
from app.db.neon import close_pool, init_pool
from app.utils.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    try:
        await init_pool()
    except Exception:
        logger.exception("Failed to initialize database pool at startup")
    yield
    await close_pool()


app = FastAPI(
    title="Citefolio API",
    description="Ask your PDF. Answers cite the page.",
    version="0.1.0",
    lifespan=lifespan,
)

_cors_origins = get_settings().cors_origin_list or ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(upload_api.router)
app.include_router(query_api.router)
app.include_router(session_api.router)
app.include_router(health_api.router)
app.include_router(feedback_api.router)
app.include_router(cleanup_api.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "citefolio", "status": "ok"}
