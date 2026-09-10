"""Embedding generation using Gemini text-embedding-004."""
import asyncio
import logging

from google import genai

from app.core.config import get_settings
from app.llm.client import get_client

logger = logging.getLogger(__name__)
settings = get_settings()


async def get_embedding(text: str) -> list[float]:
    """
    Generate a 768-dimensional embedding vector for the given text.
    Uses Gemini text-embedding-004 model.
    Raises RuntimeError if the embedding call fails.
    """
    from google.genai.types import EmbedContentConfig
    client = get_client()
    try:
        result = await asyncio.to_thread(
            client.models.embed_content,
            model=settings.gemini_embedding_model,
            contents=text,
            config=EmbedContentConfig(output_dimensionality=768)
        )
        embedding = result.embeddings[0].values
        logger.debug(
            "Embedding generated",
            extra={"model": settings.gemini_embedding_model, "dims": len(embedding)},
        )
        return embedding
    except Exception as exc:
        logger.error(
            "Embedding generation failed",
            extra={"model": settings.gemini_embedding_model, "error": str(exc)},
        )
        raise RuntimeError(f"Embedding failed: {exc}") from exc

