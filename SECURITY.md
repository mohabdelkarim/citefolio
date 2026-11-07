# Security Policy

## Supported versions

Only the `master` branch of this public demo is maintained.

## Reporting a vulnerability

Email **mohaabdelkarim2@gmail.com** with:

- Affected URL or path (`web/`, `backend/`, API route)
- What can go wrong
- How to reproduce (keep it private; no public PoC issues)

I try to reply within a few days. Please wait for a fix or a disclosure plan before posting details.

## Please do not

- Commit API keys, `DATABASE_URL`, `CRON_SECRET`, or other secrets
- Open public GitHub issues that include credentials or exploit payloads
- Use the live demo to probe unrelated systems

## Demo notes

Sessions last about two hours. Uploaded text stays only for that session and cron cleans it up. Treat the demo as public and the input as untrusted.
