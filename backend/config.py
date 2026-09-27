"""
Centralized configuration for the IntervAI backend.

Reads environment settings from backend/.env or system environment variables.
Enforces strict CORS, secure key ingestion, and active model definitions.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load backend/.env and root .env regardless of the current working directory
_BACKEND_ENV_PATH = Path(__file__).resolve().parent / ".env"
_ROOT_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if _ROOT_ENV_PATH.exists():
    load_dotenv(dotenv_path=_ROOT_ENV_PATH, override=True)
if _BACKEND_ENV_PATH.exists():
    load_dotenv(dotenv_path=_BACKEND_ENV_PATH, override=True)


class Settings:
    # --- Gemini AI ------------------------------------------------------
    @property
    def GEMINI_API_KEY(self) -> str | None:
        key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
        if not key or key in ("your_gemini_api_key_here", "INSERT_NEW_KEY_HERE"):
            return None
        return key

    @property
    def GEMINI_MODEL(self) -> str:
        # Strictly configurable via GEMINI_MODEL, defaulting to active gemini-2.5-flash
        model = (os.getenv("GEMINI_MODEL") or "gemini-2.5-flash").strip()
        return model or "gemini-2.5-flash"

    # --- Interview Configuration ----------------------------------------
    @property
    def DEFAULT_MAX_QUESTIONS(self) -> int:
        try:
            return max(3, min(15, int(os.getenv("MAX_QUESTIONS", "5"))))
        except ValueError:
            return 5

    # --- CORS Sanitization ----------------------------------------------
    # Explicitly bound to local client development and runtime origins.
    # Wildcards ("*") are strictly omitted when allow_credentials=True.
    DEFAULT_ORIGINS: list[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ]

    @property
    def allowed_origins(self) -> list[str]:
        custom_origins = os.getenv("FRONTEND_ORIGIN", "")
        origins = list(self.DEFAULT_ORIGINS)
        if custom_origins:
            for item in custom_origins.split(","):
                cleaned = item.strip()
                # Strict check: NEVER allow wildcard "*" when credentials are enabled
                if cleaned and cleaned != "*" and cleaned not in origins:
                    origins.append(cleaned)
        return origins

    @property
    def gemini_configured(self) -> bool:
        return self.GEMINI_API_KEY is not None

    @property
    def ENVIRONMENT(self) -> str:
        return (os.getenv("ENVIRONMENT") or "development").strip()

    @property
    def RATE_LIMIT_PER_MINUTE(self) -> int:
        try:
            return int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        except ValueError:
            return 60


settings = Settings()
