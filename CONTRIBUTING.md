# Contributing to Citefolio

Thanks for looking. This is a small public RAG demo. Keep PRs focused.

## Setup

1. Fork and clone the repo.
2. Follow the [README](README.md) for local `backend/` and `web/` setup.
3. Copy the env examples. Do not commit `.env` or `.env.local`.

## Workflow

1. Branch from `master` with a short name (`fix/cors_origin`, `docs/readme_badges`).
2. Prefer Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`.
3. Run what you touched:
   - Backend: `cd backend && pytest`
   - Web: `cd web && npm run build`
4. Open a PR that says what changed and how you checked it.

## Scope

- Do not add auth, multi-tenant storage, or OCR unless an issue agrees first.
- Keep the UI colors from `web/DESIGN.md` (bone / ink / ink-red). Skip purple AI themes.
- Leave `.github/workflows/pages_deploy.yml` working when you change `web/`.

## Security

Report vulnerabilities privately via [SECURITY.md](SECURITY.md). Do not open public issues with secrets or exploit details.
