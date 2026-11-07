# Citefolio

Ask your PDF. Answers cite the page.

Public portfolio RAG demo: upload a document, ask questions, get streamed answers with citations. Sessions are ephemeral (about 2 hours). No login.

## Architecture

```
Visitor → Next.js (web/) → FastAPI (backend/)
                              ├─ Voyage embeddings
                              ├─ Cohere rerank
                              ├─ Neon Postgres + pgvector
                              └─ Groq → Cerebras streaming LLM
```

Pipeline: input guard → semantic cache → HyDE/rewrite/decompose → hybrid BM25+pgvector (RRF) → retrieval guard → Cohere rerank → anti lost-in-middle context → stream answer → output guard → cache/log.

## Repository layout

- `backend/` — FastAPI API for Vercel Python
- `web/` — Next.js App Router UI

## Local setup

### 1. Neon

Create a Neon project, enable `vector`, run [`backend/app/db/schema.sql`](backend/app/db/schema.sql).

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # fill keys
uvicorn app.main:app --reload --port 8000
```

### 3. Web

```bash
cd web
npm install
copy .env.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open http://localhost:3000

## Environment variables

See [`backend/.env.example`](backend/.env.example) and [`web/.env.example`](web/.env.example).

Required for a working demo:

- `DATABASE_URL`
- `VOYAGE_API_KEY`
- `COHERE_API_KEY`
- `GROQ_API_KEY` (and ideally `CEREBRAS_API_KEY`)
- `CRON_SECRET`
- `CORS_ORIGINS` (include your web origin)
- `NEXT_PUBLIC_API_URL`

## API

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/session` | Create session |
| DELETE | `/api/session/{id}` | Destroy session + chunks |
| POST | `/api/upload` | multipart file + session_id |
| POST | `/api/query` | SSE stream: token / sources / done |
| POST | `/api/feedback` | rating 1 or -1 |
| GET | `/api/health` | dependency status |
| GET/POST | `/api/cleanup` | cron cleanup (`Authorization: Bearer CRON_SECRET`) |

## Deploy

1. **API (Vercel)** — Root Directory `backend` → https://citefolio-api.vercel.app
2. **Web (GitHub Pages)** — static export from `web/` via `.github/workflows/pages_deploy.yml` → https://mohabdelkarim.github.io/citefolio/

Set `CORS_ORIGINS` on the API to include `https://mohabdelkarim.github.io` (and local `http://localhost:3000`). Production Pages builds bake `NEXT_PUBLIC_API_URL=https://citefolio-api.vercel.app`.

Vercel Cron paths are declared in [`backend/vercel.json`](backend/vercel.json).

## Limits (v1)

- Max upload 4MB (Vercel request body limit)
- No OCR for scanned PDFs
- Managed Voyage + Cohere (no local torch models)

## License

MIT
