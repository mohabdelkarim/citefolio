# Contributing to Citefolio

Thanks for taking a look. Citefolio is a small public RAG demo; keep changes focused.

## Setup

1. Fork and clone the repo.
2. Follow [README](README.md) local setup for `backend/` and `web/`.
3. Copy env examples only; never commit `.env` / `.env.local`.

## Workflow

1. Branch from `master` with a short name (`fix/cors_origin`, `docs/readme_badges`).
2. Prefer Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`.
3. Run what you touch:
   - Backend: `cd backend && pytest`
   - Web: `cd web && npm run build`
4. Open a PR with what changed and how you verified it.

## Scope

- Do not expand the public demo into auth, multi-tenant storage, or OCR unless discussed in an issue first.
- Match the editorial UI tokens in `web/DESIGN.md` (bone / ink / ink-red). Avoid generic purple AI themes.
- Keep the Pages deploy workflow (`.github/workflows/pages_deploy.yml`) working for `web/**` changes.

## Security

Report vulnerabilities privately via [SECURITY.md](SECURITY.md). Do not open public issues for secrets or exploit details.
