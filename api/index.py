"""
FastAPI application entry point for Vercel serverless deployment.

All routes are defined in this single file. Business logic is imported
from the lib/ package (gemini_client, supabase_client, etc.).
"""

import os
import traceback
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import Body, FastAPI, Form, Request, Cookie, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from lib.gemini_client import generate_answer, get_embedding
from lib.supabase_client import (search_similar_qa, insert_qa, insert_qa_question_only, update_qa, get_stats,
    verify_login, get_channels, get_channel_by_slug, create_channel, update_channel, delete_channel,
    get_channel_stats, search_similar_qa_by_channel, insert_qa_question_only_with_channel, get_user_channels)
from lib.prompt_template import build_prompt, build_channel_prompt
from lib.html_fragments import build_generate_response_html, build_toast_html
from lib.auth import create_token, get_current_user

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str

class CreateChannelRequest(BaseModel):
    name: str
    slug: str
    description: str = ""
    system_prompt: str
    greeting_prefix: str = ""
    signature: str = ""
    color: str = "#2563EB"

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
LOGIN_PATH = STATIC_DIR / "login.html"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve the login page."""
    if not LOGIN_PATH.exists():
        return HTMLResponse(content="<h1>login.html not found</h1>", status_code=404)
    return HTMLResponse(content=LOGIN_PATH.read_text(encoding="utf-8"))


@app.post("/api/login")
async def login(body: LoginRequest, response: Response):
    """Authenticate user and set session cookie."""
    user = verify_login(body.email, body.password)
    if not user:
        return JSONResponse(content={"error": "Invalid credentials"}, status_code=401)
    token = create_token(user)
    response = JSONResponse(content={"ok": True, "name": user["name"], "role": user["role"]})
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=86400,
    )
    return response


@app.post("/api/logout")
async def logout():
    """Clear session cookie."""
    response = JSONResponse(content={"ok": True})
    response.delete_cookie("session_token")
    return response


@app.get("/api/me")
async def me(request: Request):
    """Return current user info."""
    user = get_current_user(request)
    if not user:
        return JSONResponse(content={"error": "Not authenticated"}, status_code=401)
    return JSONResponse(content={
        "id": user.get("sub"),
        "email": user.get("email"),
        "name": user.get("name"),
        "role": user.get("role"),
        "is_admin": user.get("is_admin"),
    })


@app.get("/channels", response_class=HTMLResponse)
async def channels_page(request: Request):
    """Serve the channel selection page."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    channels_path = STATIC_DIR / "channels.html"
    if not channels_path.exists():
        return HTMLResponse(content="<h1>channels.html not found</h1>", status_code=404)
    return HTMLResponse(content=channels_path.read_text(encoding="utf-8"))


@app.get("/api/channels")
async def list_channels(request: Request):
    """List all channels (or user's channels)."""
    user = get_current_user(request)
    if not user:
        return JSONResponse(content={"error": "Not authenticated"}, status_code=401)
    channels = get_channels()
    return JSONResponse(content=channels)


@app.post("/api/channels")
async def create_new_channel(request: Request, body: CreateChannelRequest):
    """Create a new channel (admin only)."""
    user = get_current_user(request)
    if not user or not user.get("is_admin"):
        return JSONResponse(content={"error": "Admin access required"}, status_code=403)
    try:
        channel = create_channel(
            name=body.name, slug=body.slug, description=body.description,
            system_prompt=body.system_prompt, greeting_prefix=body.greeting_prefix,
            signature=body.signature, color=body.color, created_by=user["sub"],
        )
        return JSONResponse(content=channel)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)


@app.get("/api/channels/{channel_slug}/stats")
async def channel_stats(request: Request, channel_slug: str):
    """Get stats for a specific channel."""
    user = get_current_user(request)
    if not user:
        return JSONResponse(content={"error": "Not authenticated"}, status_code=401)
    try:
        channel = get_channel_by_slug(channel_slug)
        if not channel:
            return JSONResponse(content={"error": "Channel not found"}, status_code=404)
        stats = get_channel_stats(channel["id"])
        return JSONResponse(content=stats)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Serve the admin page (admin only)."""
    user = get_current_user(request)
    if not user or not user.get("is_admin"):
        return RedirectResponse(url="/channels")
    admin_path = STATIC_DIR / "admin.html"
    if not admin_path.exists():
        return HTMLResponse(content="<h1>admin.html not found</h1>", status_code=404)
    return HTMLResponse(content=admin_path.read_text(encoding="utf-8"))


@app.put("/api/channels/{channel_id}")
async def update_channel_route(request: Request, channel_id: str, body: dict = Body(...)):
    """Update a channel's settings (admin only)."""
    user = get_current_user(request)
    if not user or not user.get("is_admin"):
        return JSONResponse(content={"error": "Admin access required"}, status_code=403)
    try:
        update_channel(channel_id, body)
        return JSONResponse(content={"ok": True})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)


@app.delete("/api/channels/{channel_id}")
async def delete_channel_route(request: Request, channel_id: str):
    """Delete a channel and all its Q&A data (admin only)."""
    user = get_current_user(request)
    if not user or not user.get("is_admin"):
        return JSONResponse(content={"error": "Admin access required"}, status_code=403)
    try:
        delete_channel(channel_id)
        return JSONResponse(content={"ok": True})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)


@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    """Serve the main SPA page. Redirect to channels if no channel selected."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    channel_slug = request.query_params.get("channel")
    if not channel_slug:
        return RedirectResponse(url="/channels")
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse(content="<h1>index.html not found</h1>", status_code=404)
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))


@app.post("/api/generate", response_class=HTMLResponse)
async def generate(request: Request, question: str = Form(...), channel_slug: str = Form("")):
    user = get_current_user(request)
    if not user:
        return JSONResponse(content={"error": "Not authenticated"}, status_code=401)
    try:
        query_embedding = get_embedding(question)

        if channel_slug:
            channel = get_channel_by_slug(channel_slug)
            if channel:
                similar_results = search_similar_qa_by_channel(query_embedding, channel["id"])
                prompt = build_channel_prompt(question, similar_results, channel)
                record_id = insert_qa_question_only_with_channel(question, query_embedding, channel["id"])
            else:
                similar_results = search_similar_qa(query_embedding)
                prompt = build_prompt(question, similar_results)
                record_id = insert_qa_question_only(question, query_embedding)
        else:
            similar_results = search_similar_qa(query_embedding)
            prompt = build_prompt(question, similar_results)
            record_id = insert_qa_question_only(question, query_embedding)

        draft_answer = generate_answer(prompt)
        html = build_generate_response_html(
            question=question, draft_answer=draft_answer,
            similar_results=similar_results, record_id=record_id,
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
async def learn(
    request: Request,
    question: str = Form(...),
    answer: str = Form(...),
    record_id: str = Form(""),
):
    """
    Finalize a Q&A pair: update the existing record (saved at generate time)
    with the staff-confirmed answer and re-embed with full context.
    """
    user = get_current_user(request)
    if not user:
        return JSONResponse(content={"error": "Not authenticated"}, status_code=401)
    try:
        # 1. Create embedding from combined question + answer
        combined_text = f"{question}\n\n{answer}"
        embedding = get_embedding(combined_text)

        if record_id:
            # 2a. Update existing record with finalized answer
            update_qa(
                record_id=record_id,
                answer_text=answer,
                embedding=embedding,
            )
        else:
            # 2b. Fallback: insert new record if no record_id
            insert_qa(
                question_text=question,
                answer_text=answer,
                embedding=embedding,
            )

        # 3. Return success toast HTML
        html = build_toast_html(
            message="回答を確定しました。ナレッジDBに反映済みです。",
            toast_type="success",
        )
        return HTMLResponse(content=html)

    except Exception as e:
        error_html = build_toast_html(
            message=f"保存に失敗しました: {str(e)}",
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
