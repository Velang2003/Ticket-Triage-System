"""Async Gemini LLM client wrapper with retry and structured logging."""
import asyncio
import json
import logging
import time
from typing import Any

from google import genai
from google.genai import types

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Module-level client — one per process (thread-safe)
_client: genai.Client | None = None


def get_client() -> genai.Client:
    """Return a singleton Gemini client."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


async def generate_text(
    prompt: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """
    Call the Gemini model and return the response text.
    Retries up to `settings.llm_retry_attempts` times with exponential backoff.
    Raises RuntimeError if all attempts fail.
    """
    client = get_client()
    temp = temperature if temperature is not None else settings.llm_temperature
    tokens = max_tokens if max_tokens is not None else settings.llm_max_tokens

    config = types.GenerateContentConfig(
        temperature=temp,
        max_output_tokens=tokens,
    )

    last_error: Exception | None = None
    for attempt in range(1, settings.llm_retry_attempts + 2):  # +2: initial + retries
        start = time.monotonic()
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.gemini_model,
                contents=prompt,
                config=config,
            )
            latency_ms = (time.monotonic() - start) * 1000
            logger.info(
                "LLM request succeeded",
                extra={
                    "model": settings.gemini_model,
                    "attempt": attempt,
                    "latency_ms": round(latency_ms, 2),
                    "prompt_chars": len(prompt),
                },
            )
            return response.text.strip()
        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            last_error = exc
            logger.warning(
                "LLM request failed",
                extra={
                    "model": settings.gemini_model,
                    "attempt": attempt,
                    "latency_ms": round(latency_ms, 2),
                    "error": str(exc),
                },
            )
            if attempt <= settings.llm_retry_attempts:
                await asyncio.sleep(2 ** (attempt - 1))  # 1s, 2s

    raise RuntimeError(f"LLM request failed after {settings.llm_retry_attempts + 1} attempts: {last_error}")


async def generate_json(prompt: str, retry_prompt: str | None = None) -> dict[str, Any]:
    """
    Call the LLM and parse the response as JSON.
    On parse failure retries once with retry_prompt (stricter format instruction).
    Raises ValueError if JSON cannot be parsed on both attempts.
    """
    raw = await generate_text(prompt, temperature=settings.llm_temperature)
    try:
        return _parse_json(raw)
    except ValueError as first_err:
        if retry_prompt is None:
            raise
        logger.warning("JSON parse failed on first attempt, retrying with strict prompt", extra={"error": str(first_err)})
        raw = await generate_text(retry_prompt, temperature=0.0)
        try:
            return _parse_json(raw)
        except ValueError as second_err:
            raise ValueError(f"JSON parse failed on both attempts: {second_err}") from second_err


def _parse_json(text: str) -> dict[str, Any]:
    """Strip markdown code fences if present and parse JSON."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Remove ```json ... ``` wrapper
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned
    return json.loads(cleaned)
