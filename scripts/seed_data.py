"""
Data seeding script for qa_knowledge table.

Reads a CSV file, generates embeddings via Gemini text-embedding-004,
and bulk-inserts rows into Supabase.

Usage:
    python scripts/seed_data.py
    python scripts/seed_data.py --csv path/to/other.csv
"""

import argparse
import csv
import math
import os
import time

from dotenv import load_dotenv
from google import genai
from supabase import create_client


def load_csv(csv_path: str) -> list[dict]:
    """Read the CSV and return a list of row dicts."""
    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def cleanse(rows: list[dict]) -> list[dict]:
    """Filter empty rows and remove exact duplicates. Print stats."""
    total = len(rows)

    # Map Japanese column headers to English keys
    for r in rows:
        if "お客様からの質問" in r:
            r["question_text"] = r.pop("お客様からの質問")
        if "ますびと商店の回答" in r:
            r["answer_text"] = r.pop("ますびと商店の回答")

    # Keep rows where both question_text and answer_text are non-empty
    valid = [
        r for r in rows
        if r.get("question_text", "").strip() and r.get("answer_text", "").strip()
    ]
    valid_count = len(valid)

    # Remove exact duplicates (by question_text + answer_text)
    seen = set()
    unique = []
    for r in valid:
        key = (r["question_text"].strip(), r["answer_text"].strip())
        if key not in seen:
            seen.add(key)
            unique.append(r)

    duplicates_removed = valid_count - len(unique)

    print(f"Total rows in CSV : {total}")
    print(f"Valid rows         : {valid_count}")
    print(f"Duplicates removed : {duplicates_removed}")
    print(f"Rows to process    : {len(unique)}")

    return unique


def get_embedding(client: genai.Client, text: str) -> list[float]:
    """Get a 768-dim embedding from gemini-embedding-001."""
    from google.genai import types
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=768),
    )
    return result.embeddings[0].values


def main():
    parser = argparse.ArgumentParser(description="Seed qa_knowledge table from CSV")
    parser.add_argument(
        "--csv",
        default=os.path.join(os.path.dirname(__file__), "..", "data", "qa_source.csv"),
        help="Path to the source CSV file (default: data/qa_source.csv)",
    )
    args = parser.parse_args()

    # 1. Load environment variables
    load_dotenv()

    # 2. Read CSV
    csv_path = os.path.abspath(args.csv)
    print(f"Reading CSV: {csv_path}")
    rows = load_csv(csv_path)

    # 3. Cleanse
    print()
    rows = cleanse(rows)
    if not rows:
        print("No valid rows to process. Exiting.")
        return
    print()

    # 4. Initialize clients
    gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    supabase = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_KEY"],
    )

    # 5. Process in batches of 10
    batch_size = 10
    total_batches = math.ceil(len(rows) / batch_size)
    all_records = []

    for batch_idx in range(total_batches):
        start = batch_idx * batch_size
        end = min(start + batch_size, len(rows))
        batch = rows[start:end]

        print(f"Processing batch {batch_idx + 1}/{total_batches}... (rows {start + 1}-{end})")

        for row in batch:
            question = row["question_text"].strip()
            answer = row["answer_text"].strip()
            text = question + "\n\n" + answer
            embedding = get_embedding(gemini_client, text)

            record = {
                "question_text": question,
                "answer_text": answer,
                "embedding": embedding,
            }
            # Include category if present in CSV
            if row.get("category", "").strip():
                record["category"] = row["category"].strip()

            all_records.append(record)

        # Rate limiting between batches
        if batch_idx < total_batches - 1:
            time.sleep(1)

    # 6. Bulk insert into Supabase
    print()
    print(f"Inserting {len(all_records)} records into qa_knowledge...")
    supabase.table("qa_knowledge").insert(all_records).execute()

    print(f"Done! {len(all_records)} records inserted successfully.")


if __name__ == "__main__":
    main()
