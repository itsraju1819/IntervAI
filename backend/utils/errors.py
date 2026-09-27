"""
Centralized error handling module for IntervAI.

Provides domain exception classes, async route wrappers, and FastAPI global exception handlers.
Prevents stack trace leaks and ensures standardized JSON error responses.
"""

import functools
from typing import Any, Callable, Coroutine
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from utils.logger import app_logger


class IntervAIError(Exception):
    """Base exception for all domain errors within IntervAI."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AppValidationError(IntervAIError):
    """Raised when business validation or payload constraints fail."""
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


class NotFoundError(IntervAIError):
    """Raised when an interview session or requested resource is not found."""
    def __init__(self, message: str = "Requested resource was not found.") -> None:
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class RateLimitExceededError(IntervAIError):
    """Raised when client IP exceeds permitted request threshold."""
    def __init__(self, retry_after: int) -> None:
        super().__init__(
            f"Rate limit exceeded. Try again in {retry_after} seconds.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
        self.retry_after = retry_after


class SecurityError(IntervAIError):
    """Raised when request violates security constraints (e.g. file spoofing)."""
    def __init__(self, message: str = "Security validation failed.") -> None:
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


class ExternalServiceError(IntervAIError):
    """Raised when an external dependency (such as Gemini AI) fails."""
    def __init__(self, message: str = "AI service temporarily unavailable.") -> None:
        super().__init__(message, status_code=status.HTTP_502_BAD_GATEWAY)


def with_error_handling(fn: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
    """
    Async decorator that wraps endpoint/controller methods,
    logs unexpected exceptions securely, and maps them to sanitized HTTP responses.
    """
    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await fn(*args, **kwargs)
        except IntervAIError:
            # Re-raise domain errors to be handled by domain exception handlers
            raise
        except HTTPException:
            raise
        except Exception as exc:
            app_logger.error("Unhandled exception in %s: %s", fn.__name__, exc, exc_info=True)
            raise IntervAIError("An internal server error occurred. Please try again later.") from exc
    return wrapper


def register_exception_handlers(app: FastAPI) -> None:
    """Registers centralized exception handlers on the FastAPI application instance."""

    @app.exception_handler(IntervAIError)
    async def intervai_error_handler(request: Request, exc: IntervAIError) -> JSONResponse:
        app_logger.warning("Domain error on %s %s: %s", request.method, request.url.path, exc.message)
        headers = {}
        if isinstance(exc, RateLimitExceededError):
            headers["Retry-After"] = str(exc.retry_after)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": True, "detail": exc.message, "status_code": exc.status_code},
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        app_logger.warning("Input validation failed on %s %s: %s", request.method, request.url.path, exc.errors())
        # Format field error messages cleanly for the client
        error_messages = []
        for err in exc.errors():
            loc = " -> ".join(str(loc_item) for loc_item in err.get("loc", []))
            msg = err.get("msg", "Invalid input")
            error_messages.append(f"{loc}: {msg}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": True,
                "detail": "Input validation failed.",
                "errors": error_messages,
                "status_code": status.HTTP_400_BAD_REQUEST,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": True, "detail": exc.detail, "status_code": exc.status_code},
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        app_logger.error("Unhandled server exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "detail": "An internal server error occurred. Please try again later.",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
        )
