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
