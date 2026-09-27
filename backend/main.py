"""
IntervAI backend — FastAPI application entrypoint.

Serves both the API endpoints and the static frontend so the entire
application runs seamlessly from a single unified server:
    http://localhost:8000
"""

import sys
from pathlib import Path

# Ensure backend directory and project root are in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from config import settings
    from routes.interview import router as interview_router
    from services.gemini_service import GeminiServiceError, gemini_service
    from utils.errors import ExternalServiceError, RateLimitExceededError, register_exception_handlers
    from utils.logger import app_logger
    from utils.security import SecurityHeadersMiddleware, general_limiter
except ImportError:
    from backend.config import settings
    from backend.routes.interview import router as interview_router
    from backend.services.gemini_service import GeminiServiceError, gemini_service
    from backend.utils.errors import ExternalServiceError, RateLimitExceededError, register_exception_handlers
    from backend.utils.logger import app_logger
    from backend.utils.security import SecurityHeadersMiddleware, general_limiter

app = FastAPI(
    title="IntervAI Backend",
    description="Adaptive AI interview simulation backend (FastAPI + Gemini).",
    version="1.0.0",
)

# Register centralized exception handlers for domain and unhandled errors
register_exception_handlers(app)

# Inject enterprise security headers (CSP, HSTS, X-Frame-Options, nosniff, etc.)
app.add_middleware(SecurityHeadersMiddleware)

# CORS — supports local dev, live server, and production frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Mount interview API routes
app.include_router(interview_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health_check() -> dict:
    """
    Reports whether the backend is operational and whether Gemini AI
    is currently configured with a valid API key.
    """
    return {
        "status": "ok",
        "gemini_configured": settings.gemini_configured,
        "gemini_model": settings.GEMINI_MODEL,
        "environment": settings.ENVIRONMENT,
    }


# ---------------------------------------------------------------------------
# Gemini connectivity test
# ---------------------------------------------------------------------------

class GeminiTestRequest(BaseModel):
    prompt: str = Field(
        default="Say hello and confirm you are ready to conduct a mock job interview.",
        max_length=2000,
    )


class GeminiTestResponse(BaseModel):
    reply: str


@app.post("/api/gemini/test", response_model=GeminiTestResponse)
def gemini_test(request: Request, payload: GeminiTestRequest) -> GeminiTestResponse:
    client_ip = request.client.host if request.client else "127.0.0.1"
    allowed, retry_after = general_limiter.is_allowed(client_ip)
    if not allowed:
        raise RateLimitExceededError(retry_after)

    if not gemini_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "GEMINI_API_KEY is not set on the server. Configure GEMINI_API_KEY "
                "in the server environment or backend/.env."
            ),
        )

    try:
        reply = gemini_service.generate_text(
            payload.prompt,
            system_instruction=(
                "You are IntervAI, a professional AI job interviewer. "
                "Respond in at most two sentences."
            ),
        )
    except GeminiServiceError as exc:
        app_logger.error("Gemini test call failed: %s", exc)
        raise ExternalServiceError(str(exc)) from exc

    return GeminiTestResponse(reply=reply)


# ---------------------------------------------------------------------------
# Static Frontend Serving (Unified Server)
# ---------------------------------------------------------------------------

# Mount subdirectories if they exist in ROOT_DIR
if (ROOT_DIR / "pages").exists():
    app.mount("/pages", StaticFiles(directory=ROOT_DIR / "pages"), name="pages")

if (ROOT_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=ROOT_DIR / "css"), name="css")

if (ROOT_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=ROOT_DIR / "js"), name="js")


@app.get("/")
def serve_index():
    index_file = ROOT_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "IntervAI Backend is running. Access /api/health for status."}


@app.get("/index.html")
def serve_index_html():
    return FileResponse(ROOT_DIR / "index.html")


@app.get("/setup.html")
def serve_setup_html():
    setup_file = ROOT_DIR / "pages" / "setup.html"
    if setup_file.exists():
        return FileResponse(setup_file)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="setup.html not found.")


@app.get("/interview.html")
def serve_interview_html():
    interview_file = ROOT_DIR / "pages" / "interview.html"
    if interview_file.exists():
        return FileResponse(interview_file)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="interview.html not found.")


@app.get("/results.html")
def serve_results_html():
    results_file = ROOT_DIR / "pages" / "results.html"
    if not results_file.exists():
        results_file = ROOT_DIR / "results.html"
    if results_file.exists():
        return FileResponse(results_file)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="results.html not found.")


@app.get("/style.css")
def serve_root_css():
    css_file = ROOT_DIR / "style.css"
    if css_file.exists():
        return FileResponse(css_file, media_type="text/css")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="style.css not found.")


@app.get("/script.js")
def serve_root_js():
    js_file = ROOT_DIR / "script.js"
    if js_file.exists():
        return FileResponse(js_file, media_type="application/javascript")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="script.js not found.")
