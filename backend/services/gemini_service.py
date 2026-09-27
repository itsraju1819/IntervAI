"""
GeminiService — the single place in the backend that talks to the Gemini API.

Uses the official Google GenAI SDK (`google-genai`, imported as `from google import genai`).
"""

import json
import logging

from google import genai
from google.genai import types
from google.genai.errors import APIError

try:
    from config import settings
except ImportError:
    from backend.config import settings

logger = logging.getLogger("intervai.gemini")


class GeminiServiceError(Exception):
    """Raised when Gemini cannot be reached or returns unusable output."""


class GeminiService:
    def __init__(self) -> None:
        self._cached_key: str | None = None
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client | None:
        current_key = settings.GEMINI_API_KEY
        if not current_key:
            self._client = None
            self._cached_key = None
            return None

        if self._client is None or self._cached_key != current_key:
            try:
                self._client = genai.Client(api_key=current_key)
                self._cached_key = current_key
            except Exception as exc:
                logger.error("Failed to initialize Gemini client: %s", exc)
                self._client = None
                self._cached_key = None
        return self._client

    @property
    def is_configured(self) -> bool:
        return self._get_client() is not None

    def _candidate_models(self) -> list[str]:
        models = [settings.GEMINI_MODEL, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        return list(dict.fromkeys([m for m in models if m]))

    def generate_text(self, prompt: str, *, system_instruction: str | None = None) -> str:
        """Plain-text generation with automatic model fallback."""
        client = self._get_client()
        if not client:
            raise GeminiServiceError("Gemini API key is not configured on the server.")

        last_error = None
        for model in self._candidate_models():
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                    ),
                )
                text = (response.text or "").strip()
                if text:
                    return text
            except APIError as exc:
                logger.warning("Gemini API error with model %s: %s", model, exc)
                last_error = exc
            except Exception as exc:
                logger.warning("Unexpected error with model %s: %s", model, exc)
                last_error = exc

        logger.error("All candidate Gemini models failed in generate_text: %s", last_error)
        raise GeminiServiceError("The AI service is temporarily unavailable.") from last_error

    def generate_json(
        self,
        prompt: str,
        response_schema: dict,
        *,
        system_instruction: str | None = None,
        temperature: float = 0.4,
    ) -> dict:
        """Structured-output generation matching a JSON schema with model fallback."""
        client = self._get_client()
        if not client:
            raise GeminiServiceError("Gemini API key is not configured on the server.")

        last_error = None
        for model in self._candidate_models():
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        response_schema=response_schema,
                        temperature=temperature,
                    ),
                )
                raw = (response.text or "").strip()
                if raw:
                    return json.loads(raw)
            except json.JSONDecodeError as exc:
                logger.error("Gemini returned malformed JSON with model %s: %s", model, exc)
                last_error = exc
            except APIError as exc:
                logger.warning("Gemini API error with model %s: %s", model, exc)
                last_error = exc
            except Exception as exc:
                logger.warning("Unexpected error with model %s: %s", model, exc)
                last_error = exc

        logger.error("All candidate Gemini models failed in generate_json: %s", last_error)
        raise GeminiServiceError("The AI service returned an unexpected response.") from last_error


# Shared singleton
gemini_service = GeminiService()
