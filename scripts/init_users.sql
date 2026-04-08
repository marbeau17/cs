CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'staff',
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Seed users (default password: meetsc2026)
INSERT INTO users (email, name, role, is_admin, password_hash) VALUES
('l.trabuio@meetsc.co.jp', 'Luca Trabuio', 'SW engineer', FALSE, crypt('meetsc2026', gen_salt('bf'))),
('r.agcaoili@meetsc.co.jp', 'Rafael Agcaoili', '管理者', TRUE, crypt('meetsc2026', gen_salt('bf'))),
('y.putra@meetsc.co.jp', 'Yudi Dharma Putra', 'Specialist', FALSE, crypt('meetsc2026', gen_salt('bf'))),
('y.ito@meetsc.co.jp', '伊藤 祐太', '管理者', TRUE, crypt('meetsc2026', gen_salt('bf'))),
('h.ota@meetsc.co.jp', '太田 晴瑠', 'クリエイター', FALSE, crypt('meetsc2026', gen_salt('bf'))),
('o.yasuda@meetsc.co.jp', '安田 修', '管理者', TRUE, crypt('meetsc2026', gen_salt('bf'))),
('r.watanabe@meetsc.co.jp', '渡邊 梨紗', '管理者', TRUE, crypt('meetsc2026', gen_salt('bf'))),
('m.takimiya@meetsc.co.jp', '瀧宮 誠', '管理者', TRUE, crypt('meetsc2026', gen_salt('bf'))),
('y.akimoto@meetsc.co.jp', '秋元 由美子', 'Specialist', FALSE, crypt('meetsc2026', gen_salt('bf'))),
('m.takeuchi@meetsc.co.jp', '竹内 美鈴', 'クリエイター', FALSE, crypt('meetsc2026', gen_salt('bf')))
ON CONFLICT (email) DO NOTHING;

-- RPC function to verify login
CREATE OR REPLACE FUNCTION verify_user_login(
    user_email TEXT,
    user_password TEXT
)
RETURNS TABLE (
    id UUID,
    email TEXT,
    name TEXT,
    role TEXT,
    is_admin BOOLEAN
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, u.email, u.name, u.role, u.is_admin
    FROM users u
    WHERE u.email = user_email
    AND u.password_hash = crypt(user_password, u.password_hash);
END;
$$;
