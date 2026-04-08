"""CSV import logic for bulk Q&A knowledge ingestion."""

import csv
import io
import time
from typing import Optional


def parse_csv(file_content: bytes, encoding: str = "utf-8") -> list[dict]:
    """Parse CSV content and return list of Q&A dicts.

    Supports multiple CSV formats by auto-detecting column names.
    Returns list of dicts with keys: question_text, answer_text
    """
    # Try UTF-8 first, fallback to Shift-JIS
    try:
        text = file_content.decode(encoding)
    except UnicodeDecodeError:
        try:
            text = file_content.decode("shift_jis")
        except UnicodeDecodeError:
            text = file_content.decode("utf-8", errors="replace")

    reader = csv.DictReader(io.StringIO(text))

    # Auto-detect column mapping
    headers = reader.fieldnames or []
    q_col = None
    a_col = None

    # Common patterns for question column
    for h in headers:
        h_lower = h.lower().strip()
        if any(k in h_lower for k in ["質問", "question", "お客様", "問い合わせ", "q"]):
            q_col = h
            break
    if not q_col and len(headers) >= 1:
        q_col = headers[0]

    # Common patterns for answer column
    for h in headers:
        h_lower = h.lower().strip()
        if h == q_col:
            continue
        if any(k in h_lower for k in ["回答", "answer", "返信", "response", "a"]):
            a_col = h
            break
    if not a_col and len(headers) >= 2:
        a_col = headers[1]

    if not q_col or not a_col:
        raise ValueError(f"CSVのカラムを検出できません。ヘッダー: {headers}")

    rows = []
    for row in reader:
        q = (row.get(q_col) or "").strip()
        a = (row.get(a_col) or "").strip()
        if q and a:
            rows.append({"question_text": q, "answer_text": a})

    return rows


def deduplicate(rows: list[dict]) -> list[dict]:
    """Remove exact duplicate Q&A pairs."""
    seen = set()
    unique = []
    for r in rows:
        key = (r["question_text"], r["answer_text"])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def process_csv_import(
    file_content: bytes,
    channel_id: str,
    get_embedding_fn,
    insert_fn,
    encoding: str = "utf-8",
    batch_size: int = 5,
) -> dict:
    """Process a CSV file and insert Q&A pairs into the database.

    Args:
        file_content: Raw CSV file bytes
        channel_id: Target channel ID
        get_embedding_fn: Function to generate embeddings
        insert_fn: Function to insert into DB (takes question, answer, embedding, channel_id)
        encoding: CSV file encoding
        batch_size: Number of records per batch (for rate limiting)

    Returns:
        dict with keys: total_rows, valid_rows, duplicates_removed, imported
    """
    # 1. Parse CSV
    rows = parse_csv(file_content, encoding)
    total_parsed = len(rows)

    # 2. Deduplicate
    unique_rows = deduplicate(rows)
    duplicates = total_parsed - len(unique_rows)

    # 3. Generate embeddings and insert
    imported = 0
    errors = []

    for i in range(0, len(unique_rows), batch_size):
        batch = unique_rows[i:i + batch_size]

        for row in batch:
            try:
                combined = row["question_text"] + "\n\n" + row["answer_text"]
                embedding = get_embedding_fn(combined)
                insert_fn(
                    question_text=row["question_text"],
                    answer_text=row["answer_text"],
                    embedding=embedding,
                    channel_id=channel_id,
                )
                imported += 1
            except Exception as e:
                errors.append({"row": row["question_text"][:50], "error": str(e)})

        # Rate limiting between batches
        if i + batch_size < len(unique_rows):
            time.sleep(0.5)

    return {
        "total_parsed": total_parsed,
        "duplicates_removed": duplicates,
        "imported": imported,
        "errors": len(errors),
        "error_details": errors[:5],  # Only return first 5 errors
    }
