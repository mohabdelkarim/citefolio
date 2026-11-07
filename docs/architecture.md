# Citefolio architecture

## Runtime

- **Web:** Next.js static export in `web/`, deployed to GitHub Pages (`basePath` `/citefolio` when `GITHUB_PAGES=true`).
- **API:** FastAPI in `backend/`, deployed to Vercel (`citefolio-api.vercel.app`).
- **Data:** Neon Postgres + pgvector. Document chunks use FORCE RLS keyed by `app.session_id`.

## Backend layers

| Layer | Role |
|-------|------|
| `app/api/` | HTTP only: validate, status codes, streaming wrappers |
| `app/core/` | RAG pipeline, retrieval, guards, embeddings |
| `app/db/` | Pool, SQL helpers, session checks, schema |
| `app/utils/` | Settings and eval helpers |

Query flow lives in `app/core/pipeline.py`. Keep business logic out of the routers.

## Cleanup

Vercel Cron hits `/api/cleanup?mode=all` daily. Cleanup deletes **sessions** (FK CASCADE clears documents/cache). Do not rely on bare `DELETE FROM documents` under FORCE RLS without a session GUC.

## Frontend

- `web/components/` UI
- `web/lib/` API client + session storage
- `NEXT_PUBLIC_API_URL` is the FastAPI origin
