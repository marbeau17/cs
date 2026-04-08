"""
Admin route handlers for channel management.
These will be integrated into api/index.py.
"""


# Route: PUT /api/channels/{channel_id}
# Updates a channel's settings (admin only)
async def update_channel_handler(request, channel_id: str, body: dict):
    from lib.auth import get_current_user
    from lib.supabase_client import update_channel
    user = get_current_user(request)
    if not user or not user.get("is_admin"):
        return {"error": "Admin access required"}, 403
    try:
        result = update_channel(channel_id, body)
        return result, 200
    except Exception as e:
        return {"error": str(e)}, 400


# Route: DELETE /api/channels/{channel_id}
# Deletes a channel and all its Q&A data (admin only)
async def delete_channel_handler(request, channel_id: str):
    from lib.auth import get_current_user
    from lib.supabase_client import delete_channel
    user = get_current_user(request)
    if not user or not user.get("is_admin"):
        return {"error": "Admin access required"}, 403
    try:
        delete_channel(channel_id)
        return {"ok": True}, 200
    except Exception as e:
        return {"error": str(e)}, 400


# Route: GET /admin
# Serves the admin page (admin only)
# Redirect non-admins to /channels


# === ADD THESE ROUTES TO api/index.py ===
#
# @app.get("/admin", response_class=HTMLResponse)
# async def admin_page(request: Request):
#     user = get_current_user(request)
#     if not user or not user.get("is_admin"):
#         return RedirectResponse(url="/channels")
#     admin_path = STATIC_DIR / "admin.html"
#     if not admin_path.exists():
#         return HTMLResponse(content="<h1>admin.html not found</h1>", status_code=404)
#     return HTMLResponse(content=admin_path.read_text(encoding="utf-8"))
#
# @app.put("/api/channels/{channel_id}")
# async def update_channel_route(request: Request, channel_id: str, body: dict = Body(...)):
#     user = get_current_user(request)
#     if not user or not user.get("is_admin"):
#         return JSONResponse(content={"error": "Admin access required"}, status_code=403)
#     try:
#         from lib.supabase_client import update_channel
#         result = update_channel(channel_id, body)
#         return JSONResponse(content={"ok": True})
#     except Exception as e:
#         return JSONResponse(content={"error": str(e)}, status_code=400)
#
# @app.delete("/api/channels/{channel_id}")
# async def delete_channel_route(request: Request, channel_id: str):
#     user = get_current_user(request)
#     if not user or not user.get("is_admin"):
#         return JSONResponse(content={"error": "Admin access required"}, status_code=403)
#     try:
#         from lib.supabase_client import delete_channel
#         delete_channel(channel_id)
#         return JSONResponse(content={"ok": True})
#     except Exception as e:
#         return JSONResponse(content={"error": str(e)}, status_code=400)
