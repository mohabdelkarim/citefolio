-- Citefolio schema: pgvector + session isolation via RLS

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS user_sessions (
    session_id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    ip_hash TEXT
);

CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1024) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS documents_session_id_idx
    ON documents (session_id);

CREATE INDEX IF NOT EXISTS documents_embedding_hnsw_idx
    ON documents
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS documents_session_isolation ON documents;
CREATE POLICY documents_session_isolation ON documents
    FOR ALL
    USING (
        session_id = COALESCE(
            NULLIF(current_setting('app.session_id', true), ''),
            '00000000-0000-0000-0000-000000000000'
        )::uuid
    )
    WITH CHECK (
        session_id = COALESCE(
            NULLIF(current_setting('app.session_id', true), ''),
            '00000000-0000-0000-0000-000000000000'
        )::uuid
    );

CREATE TABLE IF NOT EXISTS semantic_cache (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    query_embedding VECTOR(1024) NOT NULL,
    query_text TEXT,
    response TEXT NOT NULL,
    sources JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    hit_count INT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS semantic_cache_created_at_idx
    ON semantic_cache (created_at);

CREATE INDEX IF NOT EXISTS semantic_cache_session_id_idx
    ON semantic_cache (session_id);

-- ENABLE without FORCE: app role still filtered; table owner (cron) can prune.
ALTER TABLE semantic_cache ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS semantic_cache_session_isolation ON semantic_cache;
CREATE POLICY semantic_cache_session_isolation ON semantic_cache
    FOR ALL
    USING (
        session_id = COALESCE(
            NULLIF(current_setting('app.session_id', true), ''),
            '00000000-0000-0000-0000-000000000000'
        )::uuid
    )
    WITH CHECK (
        session_id = COALESCE(
            NULLIF(current_setting('app.session_id', true), ''),
            '00000000-0000-0000-0000-000000000000'
        )::uuid
    );

CREATE TABLE IF NOT EXISTS query_logs (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES user_sessions(session_id) ON DELETE SET NULL,
    query_text TEXT NOT NULL,
    response_text TEXT,
    provider_used TEXT,
    response_time_ms INT,
    faithfulness FLOAT,
    answer_relevancy FLOAT,
    context_precision FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS query_feedback (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES user_sessions(session_id) ON DELETE SET NULL,
    query_id BIGINT REFERENCES query_logs(id) ON DELETE CASCADE,
    rating SMALLINT NOT NULL CHECK (rating IN (-1, 1)),
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
