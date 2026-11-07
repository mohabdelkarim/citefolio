# Security Policy

## Supported versions

Only the `master` branch of this public demo is maintained.

## Reporting a vulnerability

Email **mohaabdelkarim2@gmail.com** with:

- Affected URL or path (`web/`, `backend/`, API route)
- Impact summary
- Steps to reproduce (private; no public PoC issues)

You should get an acknowledgement within a few days. Please wait for a fix or disclosure plan before posting details publicly.

## Please do not

- Commit API keys, `DATABASE_URL`, `CRON_SECRET`, or other secrets
- Open public GitHub issues that include credentials or exploit payloads
- Use the live demo to probe unrelated systems

## Demo notes

Citefolio sessions are ephemeral (~2 hours). Uploaded text is stored only for that session and cleaned by cron. Treat the demo as public and untrusted input.
