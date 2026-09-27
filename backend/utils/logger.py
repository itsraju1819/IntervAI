"""
Structured logging module for IntervAI with automatic sensitive data redaction.

Ensures all log messages include standard timestamps, log levels, component names,
and guarantees that credentials, API keys, tokens, and PII are redacted before writing.
"""

import logging
import re
import sys
from datetime import datetime, timezone

# Redaction patterns for sensitive information
PATTERNS = [
    # Google AI / Firebase API Keys
    (re.compile(r"AIza[0-9A-Za-z-_]{35}"), "[REDACTED_API_KEY]"),
    # OpenAI / generic sk- style secret keys
    (re.compile(r"sk-[a-zA-Z0-9_\-]{16,}"), "[REDACTED_SECRET_KEY]"),
    # Bearer tokens
    (re.compile(r"(Bearer\s+)[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_=]*", re.IGNORECASE), r"\1[REDACTED_JWT]"),
    # Key / password / secret in key=value or JSON formats
    (re.compile(r'("(?:api_?key|password|secret|token|credential)"\s*:\s*")[^"]+(")', re.IGNORECASE), r"\1[REDACTED]\2"),
    (re.compile(r'((?:api_?key|password|secret|token)=)[^\s&]+', re.IGNORECASE), r"\1[REDACTED]"),
    # Email addresses (PII)
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    # Phone numbers (PII, standard 10+ digits formats)
    (re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[REDACTED_PHONE]"),
]


class SensitiveDataFilter(logging.Filter):
    """Filter that masks passwords, tokens, API keys, and PII from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.redact(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.redact(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.redact(str(arg)) for arg in record.args)
        return True

    @staticmethod
    def redact(text: str) -> str:
        if not text:
            return ""
        result = text
        for pattern, replacement in PATTERNS:
            result = pattern.sub(replacement, result)
        return result


class StructuredFormatter(logging.Formatter):
    """Formats logs with ISO 8601 UTC timestamps and consistent component alignment."""

    def format(self, record: logging.LogRecord) -> str:
        record.asctime = datetime.now(timezone.utc).isoformat()
        return super().format(record)


def setup_logger(name: str = "intervai") -> logging.Logger:
    """Configures and returns a structured, redaction-safe logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = StructuredFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


# Global structured application logger
app_logger = setup_logger("intervai")
