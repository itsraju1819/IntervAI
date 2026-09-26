"""
Centralized configuration for the IntervAI backend.

Reads environment settings from backend/.env or system environment variables.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env regardless of the current working directory the
# server is started from.
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=True)


class Settings:
    # --- Gemini ---------------------------------------------------------
    @property
    def GEMINI_API_KEY(self) -> str | None:
        key = (os.getenv("GEMINI_API_KEY") or "").strip()
        if not key or key == "your_gemini_api_key_here":
            return None
        return key

    @property
    def GEMINI_MODEL(self) -> str:
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        # Protect against legacy invalid model string
        if model == "gemini-3.5-flash":
            return "gemini-2.5-flash"
        return model or "gemini-2.5-flash"

    # --- CORS -------------------------------------------------------------
    FRONTEND_ORIGIN: str = os.getenv(
        "FRONTEND_ORIGIN",
        "http://localhost:5500,http://127.0.0.1:5500,"
        "http://localhost:8000,http://127.0.0.1:8000,"
        "http://localhost:3000,http://127.0.0.1:3000",
    )

    @property
    def allowed_origins(self) -> list[str]:
        origins = [o.strip() for o in self.FRONTEND_ORIGIN.split(",") if o.strip()]
        if "null" not in origins:
            origins.append("null")
        if "*" not in origins:
            origins.append("*")
        return origins

    @property
    def gemini_configured(self) -> bool:
        return self.GEMINI_API_KEY is not None


settings = Settings()
