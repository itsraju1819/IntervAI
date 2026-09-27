"""
Security utilities and middleware for the IntervAI application.

Provides input sanitization, file signature validation, security headers middleware,
and in-memory rate limiting to defend against XSS, injection, MIME spoofing, and DoS.
"""

import html
import re
import time
from collections import defaultdict
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Regex for stripping dangerous script/HTML tags while preserving basic punctuation
TAG_RE = re.compile(r"<[^>]+>", re.IGNORECASE)
NULL_BYTE_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
DANGEROUS_URI_SCHEMES = re.compile(r"(javascript:|data:|vbscript:)", re.IGNORECASE)


def sanitize_text(value: str | None, max_length: int = 15000) -> str:
    """
    Sanitizes user-provided text inputs:
    - Truncates to max_length to protect against DoS
    - Strips null bytes and terminal control characters
    - Strips HTML tags and dangerous URI schemes
    - Escapes residual HTML entities
    """
    if not value:
        return ""

    # Bound input length
    sanitized = str(value)[:max_length]

    # Remove null bytes and control characters
    sanitized = NULL_BYTE_RE.sub("", sanitized)

    # Strip script/HTML tags
    sanitized = TAG_RE.sub("", sanitized)

    # Neutralize dangerous URI schemes
    sanitized = DANGEROUS_URI_SCHEMES.sub("", sanitized)

    # Escape HTML special characters for safe output and downstream rendering
    sanitized = html.escape(sanitized, quote=True)

    return sanitized.strip()


def validate_pdf_signature(content: bytes, max_bytes: int = 10 * 1024 * 1024) -> bool:
    """
    Validates that file content has a genuine PDF header (%PDF-)
    and does not exceed maximum byte limit (default: 10MB).
    Defeats MIME-type spoofing and malicious file extension attacks.
    """
    if not content:
        return False

    if len(content) > max_bytes:
        return False

    # PDF magic number signature check: must start with '%PDF-' within the first 1024 bytes
    header_chunk = content[:1024]
    return b"%PDF-" in header_chunk


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware injecting robust security headers into all responses:
    - Content-Security-Policy (CSP)
    - Strict-Transport-Security (HSTS)
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)

        # Enforce strict Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com data:",
            "img-src 'self' data:",
            "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000 http://localhost:3000 http://127.0.0.1:3000 http://localhost:5500 http://127.0.0.1:5500",
            "frame-ancestors 'none'",
            "object-src 'none'",
            "base-uri 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(self), geolocation=()"

        # Enforce HSTS if request was served over HTTPS or forwarded by a proxy
        if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


class RateLimiter:
    """
    In-memory sliding window rate limiter per client IP.
    Protects compute-intensive endpoints (AI generation, resume uploads) from brute-force/DoS.
    """
    def __init__(
        self,
        requests_per_minute: int = 60,
        window_seconds: float = 60.0,
        requests_per_window: int | None = None,
    ) -> None:
        self.limit = requests_per_window if requests_per_window is not None else requests_per_minute
        self.window = float(window_seconds)
        self._history: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> tuple[bool, int]:
        now = time.time()
        timestamps = self._history[client_ip]

        # Purge entries older than sliding window
        valid_timestamps = [t for t in timestamps if now - t < self.window]
        self._history[client_ip] = valid_timestamps

        if len(valid_timestamps) >= self.limit:
            retry_after = int(self.window - (now - valid_timestamps[0])) + 1
            return False, max(1, retry_after)

        self._history[client_ip].append(now)
        return True, 0


# Shared rate limiter instances
general_limiter = RateLimiter(requests_per_minute=60)
upload_limiter = RateLimiter(requests_per_minute=15)
