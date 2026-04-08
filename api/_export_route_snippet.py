# === Route to add to api/index.py ===
#
# @app.get("/api/channels/{channel_slug}/export")
# async def export_csv(request: Request, channel_slug: str):
#     """Export channel knowledge as CSV download."""
#     user = get_current_user(request)
#     if not user:
#         return JSONResponse(content={"error": "Not authenticated"}, status_code=401)
#     try:
#         channel = get_channel_by_slug(channel_slug)
#         if not channel:
#             return JSONResponse(content={"error": "Channel not found"}, status_code=404)
#
#         from lib.supabase_client import get_client
#         client = get_client()
#         result = client.table("qa_knowledge").select(
#             "question_text, answer_text, created_at"
#         ).eq("channel_id", channel["id"]).order("created_at").execute()
#
#         import csv, io
#         output = io.StringIO()
#         writer = csv.writer(output)
#         writer.writerow(["質問", "回答", "作成日時"])
#         for row in result.data:
#             writer.writerow([row["question_text"], row["answer_text"], row["created_at"]])
#
#         from fastapi.responses import StreamingResponse
#         content = output.getvalue().encode("utf-8-sig")  # BOM for Excel compatibility
#         return Response(
#             content=content,
#             media_type="text/csv",
#             headers={"Content-Disposition": f"attachment; filename={channel_slug}_knowledge.csv"}
#         )
#     except Exception as e:
#         return JSONResponse(content={"error": str(e)}, status_code=500)
