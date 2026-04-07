import os

from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def get_embedding(text: str) -> list[float]:
    """Return the embedding vector (768 dimensions) for the given text."""
    result = client.models.embed_content(
        model="text-embedding-004",
        contents=text,
    )
    return result.embeddings[0].values


def generate_answer(prompt: str) -> str:
    """Generate a text response from Gemini 2.5 Pro."""
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
    )
    return response.text
