"""
FastAPI application entry point for Vercel serverless deployment.

All routes are defined in this single file. Business logic is imported
from the lib/ package (gemini_client, supabase_client, etc.).
"""

import os
import traceback
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from lib.gemini_client import generate_answer, get_embedding
from lib.supabase_client import search_similar_qa, insert_qa, get_stats
from lib.prompt_template import build_prompt
from lib.html_fragments import build_generate_response_html, build_toast_html

# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------

app = FastAPI(title="ますびと商店 CS Support AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to static/index.html (relative to project root)
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main SPA page."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse(
            content="<h1>index.html not found</h1>",
            status_code=404,
        )
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))


@app.post("/api/generate", response_class=HTMLResponse)
async def generate(question: str = Form(...)):
    """
    Accept a customer question, find similar past Q&A via vector search,
    build a prompt, call Gemini for a draft answer, and return an HTML
    fragment (editor area + reference cards) for htmx to swap in.
    """
    try:
        # 1. Embed the incoming question
        query_embedding = get_embedding(question)

        # 2. Search Supabase for similar Q&A (top 3)
        similar_results = search_similar_qa(query_embedding)

        # 3. Build the prompt with context
        prompt = build_prompt(question, similar_results)

        # 4. Generate answer draft via Gemini
        draft_answer = generate_answer(prompt)

        # 5. Build the HTML response (editor + reference cards)
        html = build_generate_response_html(
            question=question,
            draft_answer=draft_answer,
            similar_results=similar_results,
        )
        return HTMLResponse(content=html)

    except Exception as e:
        error_html = (
            '<div class="p-4 bg-red-50 border border-red-200 rounded-lg">'
            '<p class="text-red-700 font-semibold">エラーが発生しました</p>'
            f'<p class="text-red-600 text-sm mt-1">{str(e)}</p>'
            "</div>"
        )
        traceback.print_exc()
        return HTMLResponse(content=error_html, status_code=500)


@app.post("/api/learn", response_class=HTMLResponse)
async def learn(question: str = Form(...), answer: str = Form(...)):
    """
    Learn a confirmed Q&A pair: embed the combined text, insert into
    Supabase, and return a toast notification HTML fragment.
    """
    try:
        # 1. Create embedding from combined question + answer
        combined_text = f"{question}\n\n{answer}"
        embedding = get_embedding(combined_text)

        # 2. Insert into Supabase
        insert_qa(
            question_text=question,
            answer_text=answer,
            embedding=embedding,
        )

        # 3. Return success toast HTML
        html = build_toast_html(
            message="学習が完了しました",
            toast_type="success",
        )
        return HTMLResponse(content=html)

    except Exception as e:
        error_html = build_toast_html(
            message=f"学習に失敗しました: {str(e)}",
            toast_type="error",
        )
        traceback.print_exc()
        return HTMLResponse(content=error_html, status_code=500)


@app.get("/api/stats")
async def stats():
    """Return knowledge-base statistics as JSON."""
    try:
        data = get_stats()
        return JSONResponse(content=data)
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
        )
