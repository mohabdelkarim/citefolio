-- SQL executed by POST /api/cleanup (Vercel Cron). Not pg_cron-only:
-- Neon scale-to-zero would skip in-database schedules while idle.

-- Hourly: drop document chunks older than session TTL window (2 hours)
DELETE FROM documents
WHERE created_at < NOW() - INTERVAL '2 hours';

-- Hourly: drop expired sessions (cascades remaining docs via FK)
DELETE FROM user_sessions
WHERE expires_at < NOW();

-- Daily safety net: purge any documents older than 24 hours
DELETE FROM documents
WHERE created_at < NOW() - INTERVAL '24 hours';

-- Weekly: prune semantic cache older than 7 days
DELETE FROM semantic_cache
WHERE created_at < NOW() - INTERVAL '7 days';
