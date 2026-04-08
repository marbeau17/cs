import os
from supabase import create_client, Client


def get_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    return create_client(url, key)


def search_similar_qa(
    query_embedding: list[float],
    match_count: int = 3,
    match_threshold: float = 0.5,
) -> list[dict]:
    client = get_client()
    result = client.rpc("match_qa_knowledge", {
        "query_embedding": query_embedding,
        "match_threshold": match_threshold,
        "match_count": match_count,
    }).execute()
    return result.data


def insert_qa(
    question_text: str,
    answer_text: str,
    embedding: list[float],
) -> dict:
    client = get_client()
    result = client.table("qa_knowledge").insert({
        "question_text": question_text,
        "answer_text": answer_text,
        "embedding": embedding,
    }).execute()
    return result.data


def insert_qa_question_only(
    question_text: str,
    embedding: list[float],
) -> str:
    """Insert a question with empty answer. Returns the record ID."""
    client = get_client()
    result = client.table("qa_knowledge").insert({
        "question_text": question_text,
        "answer_text": "",
        "embedding": embedding,
    }).execute()
    return result.data[0]["id"]


def update_qa(
    record_id: str,
    answer_text: str,
    embedding: list[float],
) -> dict:
    """Update an existing record with the finalized answer and new embedding."""
    client = get_client()
    result = client.table("qa_knowledge").update({
        "answer_text": answer_text,
        "embedding": embedding,
    }).eq("id", record_id).execute()
    return result.data


def verify_login(email: str, password: str):
    """Verify user credentials via Supabase RPC. Returns user dict or None."""
    client = get_client()
    result = client.rpc("verify_user_login", {
        "user_email": email,
        "user_password": password,
    }).execute()
    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


def get_stats() -> dict:
    client = get_client()
    count_result = client.table("qa_knowledge").select("id", count="exact").execute()
    last_result = (
        client.table("qa_knowledge")
        .select("created_at")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return {
        "total_records": count_result.count,
        "last_learned_at": last_result.data[0]["created_at"] if last_result.data else None,
    }


# --- Channel management ---

def get_channels() -> list:
    """Get all channels."""
    client = get_client()
    result = client.table("channels").select("*").order("created_at").execute()
    return result.data


def get_channel(channel_id: str) -> dict:
    """Get a single channel by ID."""
    client = get_client()
    result = client.table("channels").select("*").eq("id", channel_id).single().execute()
    return result.data


def get_channel_by_slug(slug: str) -> dict:
    """Get a single channel by slug."""
    client = get_client()
    result = client.table("channels").select("*").eq("slug", slug).single().execute()
    return result.data


def create_channel(name: str, slug: str, description: str, system_prompt: str,
                   greeting_prefix: str, signature: str, color: str, created_by: str) -> dict:
    """Create a new channel."""
    client = get_client()
    result = client.table("channels").insert({
        "name": name,
        "slug": slug,
        "description": description,
        "system_prompt": system_prompt,
        "greeting_prefix": greeting_prefix,
        "signature": signature,
        "color": color,
        "created_by": created_by,
    }).execute()
    return result.data[0] if result.data else None


def update_channel(channel_id: str, updates: dict) -> dict:
    """Update a channel's settings."""
    client = get_client()
    result = client.table("channels").update(updates).eq("id", channel_id).execute()
    return result.data


def delete_channel(channel_id: str) -> None:
    """Delete a channel and its Q&A data."""
    client = get_client()
    client.table("qa_knowledge").delete().eq("channel_id", channel_id).execute()
    client.table("channels").delete().eq("id", channel_id).execute()


def search_similar_qa_by_channel(query_embedding: list, channel_id: str,
                                  match_count: int = 3, match_threshold: float = 0.5) -> list:
    """Search similar Q&A within a specific channel."""
    client = get_client()
    result = client.rpc("match_qa_knowledge_by_channel", {
        "query_embedding": query_embedding,
        "p_channel_id": channel_id,
        "match_threshold": match_threshold,
        "match_count": match_count,
    }).execute()
    return result.data


def insert_qa_with_channel(question_text: str, answer_text: str,
                           embedding: list, channel_id: str) -> dict:
    """Insert a Q&A pair into a specific channel."""
    client = get_client()
    result = client.table("qa_knowledge").insert({
        "question_text": question_text,
        "answer_text": answer_text,
        "embedding": embedding,
        "channel_id": channel_id,
    }).execute()
    return result.data


def insert_qa_question_only_with_channel(question_text: str, embedding: list, channel_id: str) -> str:
    """Insert question with empty answer into a specific channel. Returns record ID."""
    client = get_client()
    result = client.table("qa_knowledge").insert({
        "question_text": question_text,
        "answer_text": "",
        "embedding": embedding,
        "channel_id": channel_id,
    }).execute()
    return result.data[0]["id"]


def get_channel_stats(channel_id: str) -> dict:
    """Get stats for a specific channel."""
    client = get_client()
    count_result = client.table("qa_knowledge").select("id", count="exact").eq("channel_id", channel_id).execute()
    last_result = (
        client.table("qa_knowledge")
        .select("created_at")
        .eq("channel_id", channel_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return {
        "total_records": count_result.count,
        "last_learned_at": last_result.data[0]["created_at"] if last_result.data else None,
    }


def get_user_channels(user_id: str) -> list:
    """Get channels a user has access to."""
    client = get_client()
    result = client.table("channel_members").select("channel_id, channels(*)").eq("user_id", user_id).execute()
    return [item["channels"] for item in result.data if item.get("channels")]


def add_channel_member(channel_id: str, user_id: str, role: str = "member") -> None:
    """Add a user to a channel."""
    client = get_client()
    client.table("channel_members").insert({
        "channel_id": channel_id,
        "user_id": user_id,
        "role": role,
    }).execute()


def get_channel_knowledge(channel_id: str, page: int = 1, per_page: int = 20) -> dict:
    """Get paginated Q&A entries for a channel."""
    client = get_client()
    offset = (page - 1) * per_page

    count_result = client.table("qa_knowledge").select("id", count="exact").eq("channel_id", channel_id).execute()

    data_result = (
        client.table("qa_knowledge")
        .select("id, question_text, answer_text, created_at")
        .eq("channel_id", channel_id)
        .order("created_at", desc=True)
        .range(offset, offset + per_page - 1)
        .execute()
    )

    return {
        "data": data_result.data,
        "total": count_result.count,
        "page": page,
        "per_page": per_page,
    }


def delete_qa(record_id: str) -> None:
    """Delete a single Q&A entry."""
    client = get_client()
    client.table("qa_knowledge").delete().eq("id", record_id).execute()
