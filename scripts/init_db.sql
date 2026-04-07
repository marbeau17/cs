-- ============================================================
-- Supabase Database Initialization
-- ============================================================

-- 1. Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Create qa_knowledge table
CREATE TABLE IF NOT EXISTS qa_knowledge (
    id              UUID                     PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_text   TEXT                     NOT NULL,
    answer_text     TEXT                     NOT NULL,
    embedding       vector(768)              NOT NULL,
    category        TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create HNSW index on embedding column for cosine similarity search
CREATE INDEX IF NOT EXISTS qa_knowledge_embedding_idx
    ON qa_knowledge
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- 4. RPC function: match_qa_knowledge
--    Returns the top matches by cosine similarity above a given threshold.
CREATE OR REPLACE FUNCTION match_qa_knowledge(
    query_embedding  vector(768),
    match_threshold  float DEFAULT 0.5,
    match_count      int   DEFAULT 3
)
RETURNS TABLE (
    id              UUID,
    question_text   TEXT,
    answer_text     TEXT,
    similarity      float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        qk.id,
        qk.question_text,
        qk.answer_text,
        1 - (qk.embedding <=> query_embedding) AS similarity
    FROM qa_knowledge qk
    WHERE 1 - (qk.embedding <=> query_embedding) >= match_threshold
    ORDER BY qk.embedding <=> query_embedding
    LIMIT match_count;
$$;
