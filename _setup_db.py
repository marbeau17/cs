#!/usr/bin/env python3
"""Set up users table and seed data in Supabase via direct DB connection (forced IPv4)."""
import json
import socket

# Force IPv4 to avoid IPv6 routing issues
_original_getaddrinfo = socket.getaddrinfo
def _ipv4_only_getaddrinfo(*args, **kwargs):
    results = _original_getaddrinfo(*args, **kwargs)
    return [r for r in results if r[0] == socket.AF_INET] or results
socket.getaddrinfo = _ipv4_only_getaddrinfo

import psycopg2

def run():
    print("Connecting to database via session-mode pooler...")
    # Session mode pooler (port 5432) supports prepared statements and extensions
    conn = psycopg2.connect(
        host="aws-0-ap-northeast-1.pooler.supabase.com",
        port=5432,
        dbname="postgres",
        user="postgres.mavjmydnmgeimtilvsbt",
        password="Narashi21&&",
        connect_timeout=15,
    )
    conn.autocommit = True
    cur = conn.cursor()
    print("Connected!")

    # Step 1: Enable pgcrypto
    print("\n1. Enabling pgcrypto extension...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    print("   Done.")

    # Step 2: Create users table
    print("2. Creating users table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'staff',
            is_admin BOOLEAN NOT NULL DEFAULT FALSE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)
    print("   Done.")

    # Step 3: Insert users
    print("3. Inserting users...")
    users = [
        ("l.trabuio@meetsc.co.jp", "Luca Trabuio", "SW engineer", False),
        ("r.agcaoili@meetsc.co.jp", "Rafael Agcaoili", "管理者", True),
        ("y.putra@meetsc.co.jp", "Yudi Dharma Putra", "Specialist", False),
        ("y.ito@meetsc.co.jp", "伊藤 祐太", "管理者", True),
        ("h.ota@meetsc.co.jp", "太田 晴瑠", "クリエイター", False),
        ("o.yasuda@meetsc.co.jp", "安田 修", "管理者", True),
        ("r.watanabe@meetsc.co.jp", "渡邊 梨紗", "管理者", True),
        ("m.takimiya@meetsc.co.jp", "瀧宮 誠", "管理者", True),
        ("y.akimoto@meetsc.co.jp", "秋元 由美子", "Specialist", False),
        ("m.takeuchi@meetsc.co.jp", "竹内 美鈴", "クリエイター", False),
    ]

    for email, name, role, is_admin in users:
        cur.execute("""
            INSERT INTO users (email, name, role, is_admin, password_hash)
            VALUES (%s, %s, %s, %s, crypt('meetsc2026', gen_salt('bf')))
            ON CONFLICT (email) DO NOTHING;
        """, (email, name, role, is_admin))
        print(f"   Inserted: {email} ({name})")

    # Step 4: Create verify_user_login function
    print("4. Creating verify_user_login RPC function...")
    cur.execute("""
        CREATE OR REPLACE FUNCTION verify_user_login(user_email TEXT, user_password TEXT)
        RETURNS TABLE (id UUID, email TEXT, name TEXT, role TEXT, is_admin BOOLEAN)
        LANGUAGE plpgsql AS $$
        BEGIN
            RETURN QUERY
            SELECT u.id, u.email, u.name, u.role, u.is_admin
            FROM users u
            WHERE u.email = user_email
            AND u.password_hash = crypt(user_password, u.password_hash);
        END;
        $$;
    """)
    print("   Done.")

    # Step 5: Verify
    print("5. Verifying users table...")
    cur.execute("SELECT email, name, role, is_admin FROM users ORDER BY email;")
    rows = cur.fetchall()
    print(f"   Found {len(rows)} users:")
    print(f"   {'Email':<30} {'Name':<20} {'Role':<15} {'Admin'}")
    print(f"   {'-'*30} {'-'*20} {'-'*15} {'-'*5}")
    for row in rows:
        print(f"   {row[0]:<30} {row[1]:<20} {row[2]:<15} {row[3]}")

    # Step 6: Test login function
    print("\n6. Testing verify_user_login with o.yasuda@meetsc.co.jp...")
    cur.execute("SELECT * FROM verify_user_login('o.yasuda@meetsc.co.jp', 'meetsc2026');")
    result = cur.fetchall()
    if result:
        print(f"   Login test SUCCESS: {result[0]}")
    else:
        print("   Login test FAILED: no result returned")

    cur.close()
    conn.close()
    print("\nAll done!")

if __name__ == "__main__":
    run()
