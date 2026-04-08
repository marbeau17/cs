-- Channels table: each channel represents a different CS use case / business
CREATE TABLE IF NOT EXISTS channels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT DEFAULT '',
    system_prompt TEXT NOT NULL,
    greeting_prefix TEXT DEFAULT 'お客様
いつも大変お世話になっております。',
    signature TEXT DEFAULT '',
    color TEXT DEFAULT '#2563EB',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add channel_id to qa_knowledge (nullable for backward compat with existing data)
ALTER TABLE qa_knowledge ADD COLUMN IF NOT EXISTS channel_id UUID REFERENCES channels(id);

-- Create index on channel_id for faster filtering
CREATE INDEX IF NOT EXISTS idx_qa_knowledge_channel ON qa_knowledge(channel_id);

-- Seed default channel for existing data (ますびと商店)
INSERT INTO channels (id, name, slug, description, system_prompt, greeting_prefix, signature, color)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'ますびと商店',
    'masubito',
    '釣具ECサイト「ますびと商店」のカスタマーサポート',
    'あなたは釣具ECサイト「ますびと商店」のベテランカスタマーサポートです。
以下の【過去の対応ナレッジ】を参考に、【顧客からの新規問い合わせ】に対する丁寧な返信メールのドラフトを作成してください。',
    'お客様
いつも大変お世話になっております。',
    'ますびと商店',
    '#2563EB'
)
ON CONFLICT (slug) DO NOTHING;

-- Update existing qa_knowledge records to belong to default channel
UPDATE qa_knowledge SET channel_id = '00000000-0000-0000-0000-000000000001' WHERE channel_id IS NULL;

-- Updated match function that filters by channel_id
CREATE OR REPLACE FUNCTION match_qa_knowledge_by_channel(
    query_embedding vector(768),
    p_channel_id UUID,
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 3
)
RETURNS TABLE (
    id UUID,
    question_text TEXT,
    answer_text TEXT,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        qk.id,
        qk.question_text,
        qk.answer_text,
        1 - (qk.embedding <=> query_embedding) AS similarity
    FROM qa_knowledge qk
    WHERE qk.channel_id = p_channel_id
    AND 1 - (qk.embedding <=> query_embedding) >= match_threshold
    ORDER BY qk.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Channel members: which users have access to which channels
CREATE TABLE IF NOT EXISTS channel_members (
    channel_id UUID REFERENCES channels(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'member',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (channel_id, user_id)
);

-- Add all existing users to the default channel
INSERT INTO channel_members (channel_id, user_id)
SELECT '00000000-0000-0000-0000-000000000001', id FROM users
ON CONFLICT DO NOTHING;
