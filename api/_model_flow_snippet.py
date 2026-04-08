# === Changes needed in api/index.py generate route ===
#
# After: draft_answer = generate_answer(prompt, model=model)
# Determine the actual model used:
#     from lib.gemini_client import AVAILABLE_MODELS, DEFAULT_MODEL
#     actual_model = model if model in AVAILABLE_MODELS else DEFAULT_MODEL
#     model_name = AVAILABLE_MODELS[actual_model]["name"]
#
# Then pass to html builder:
#     html = build_generate_response_html(
#         question=question, draft_answer=draft_answer,
#         similar_results=similar_results, record_id=record_id,
#         model_used=model_name,
#     )
