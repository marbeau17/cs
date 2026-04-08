# Add this route to api/index.py after the admin routes, before GET /

# @app.get("/import", response_class=HTMLResponse)
# async def import_page(request: Request):
#     """Serve the CSV import page (admin only)."""
#     user = get_current_user(request)
#     if not user or not user.get("is_admin"):
#         return RedirectResponse(url="/channels")
#     import_path = STATIC_DIR / "import.html"
#     if not import_path.exists():
#         return HTMLResponse(content="<h1>import.html not found</h1>", status_code=404)
#     return HTMLResponse(content=import_path.read_text(encoding="utf-8"))
