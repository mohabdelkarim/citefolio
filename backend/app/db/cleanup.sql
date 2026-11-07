-- SQL mirror of POST /api/cleanup (Vercel Cron). Not pg_cron-only:
-- Neon scale-to-zero would skip in-database schedules while idle.
--
-- documents has FORCE ROW LEVEL SECURITY, so bare DELETE FROM documents
-- without set_config('app.session_id', ...) only hits the nil UUID.
-- Prefer deleting sessions; FK CASCADE removes documents and cache rows.

-- Hourly / all: drop expired sessions (cascades docs + session-scoped cache)
DELETE FROM user_sessions
WHERE expires_at < NOW();

-- Daily / all: age-cap sessions (12x SESSION_TTL_HOURS; default 24h)
DELETE FROM user_sessions
WHERE created_at < NOW() - make_interval(hours => 24);

-- Weekly / all: prune semantic cache older than 7 days
DELETE FROM semantic_cache
WHERE created_at < NOW() - INTERVAL '7 days';
