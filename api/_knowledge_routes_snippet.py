# === Routes to add to api/index.py ===

# GET /api/channels/{channel_slug}/knowledge
# List Q&A entries for a channel (paginated)
#
# @app.get("/api/channels/{channel_slug}/knowledge")
# async def list_knowledge(request: Request, channel_slug: str, page: int = 1, per_page: int = 20):
#     user = get_current_user(request)
#     if not user:
#         return JSONResponse(content={"error": "Not authenticated"}, status_code=401)
#     try:
#         channel = get_channel_by_slug(channel_slug)
#         if not channel:
#             return JSONResponse(content={"error": "Channel not found"}, status_code=404)
#         from lib.supabase_client import get_channel_knowledge
#         data = get_channel_knowledge(channel["id"], page, per_page)
#         return JSONResponse(content=data)
#     except Exception as e:
#         return JSONResponse(content={"error": str(e)}, status_code=500)

# DELETE /api/knowledge/{record_id}
# Delete a single Q&A entry
#
# @app.delete("/api/knowledge/{record_id}")
# async def delete_knowledge(request: Request, record_id: str):
#     user = get_current_user(request)
#     if not user or not user.get("is_admin"):
#         return JSONResponse(content={"error": "Admin required"}, status_code=403)
#     try:
#         from lib.supabase_client import delete_qa
#         delete_qa(record_id)
#         return JSONResponse(content={"ok": True})
#     except Exception as e:
#         return JSONResponse(content={"error": str(e)}, status_code=500)
