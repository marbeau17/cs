import os

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def get_embedding(text: str) -> list[float]:
    """Return the embedding vector (768 dimensions) for the given text."""
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=768),
    )
    return result.embeddings[0].values


# Available models for generation
AVAILABLE_MODELS = {
    "gemini-flash-latest": {"name": "Gemini Flash Latest", "description": "最新Flash（デフォルト）", "cost": "$0.30/$2.50"},
    "gemini-2.5-flash": {"name": "Gemini 2.5 Flash", "description": "高速・低コスト", "cost": "$0.15/$0.60"},
    "gemini-2.5-pro": {"name": "Gemini 2.5 Pro", "description": "高品質・思考モデル", "cost": "$1.25/$10.00"},
    "gemini-2.0-flash": {"name": "Gemini 2.0 Flash", "description": "安定版", "cost": "$0.10/$0.40"},
    "gemini-2.0-flash-lite": {"name": "Gemini 2.0 Flash Lite", "description": "最軽量・最速", "cost": "$0.075/$0.30"},
    "gemini-3.1-pro-preview": {"name": "Gemini 3.1 Pro Preview", "description": "最新・最高品質", "cost": "Preview"},
    "gemini-3-flash-preview": {"name": "Gemini 3 Flash Preview", "description": "次世代Flash", "cost": "Preview"},
}

DEFAULT_MODEL = "gemini-flash-latest"


def generate_answer(prompt: str, model: str = "") -> str:
    """Generate a text response using the specified Gemini model."""
    model_id = model if model in AVAILABLE_MODELS else DEFAULT_MODEL
    response = client.models.generate_content(
        model=model_id,
        contents=prompt,
    )
    return response.text


def list_available_models() -> list:
    """Return list of available models with metadata."""
    return [
        {"id": k, "name": v["name"], "description": v["description"], "cost": v["cost"]}
        for k, v in AVAILABLE_MODELS.items()
    ]
