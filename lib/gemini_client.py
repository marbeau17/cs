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


def generate_answer(prompt: str) -> str:
    """Generate a text response from Gemini 2.5 Pro."""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text
