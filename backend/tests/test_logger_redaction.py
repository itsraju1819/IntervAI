"""
Unit tests for structured logging and sensitive data redaction.
"""

import io
import logging
from backend.utils.logger import SensitiveDataFilter, StructuredFormatter


class TestSensitiveDataRedaction:
    """Verifies that credentials, tokens, API keys, and PII are redacted from logs."""

    def test_redacts_google_api_key(self):
        secret_log = "Initializing Gemini with key: ***REMOVED***"
        redacted = SensitiveDataFilter.redact(secret_log)
        assert "AIzaSy" not in redacted
        assert "[REDACTED_API_KEY]" in redacted

    def test_redacts_secret_sk_key(self):
        secret_log = "Using external key sk-proj-1234567890abcdef12345678"
        redacted = SensitiveDataFilter.redact(secret_log)
        assert "1234567890" not in redacted
        assert "[REDACTED_SECRET_KEY]" in redacted

    def test_redacts_bearer_token(self):
        auth_header = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.signature"
        redacted = SensitiveDataFilter.redact(auth_header)
        assert "eyJhbGci" not in redacted
        assert "[REDACTED_JWT]" in redacted

    def test_redacts_json_passwords_and_secrets(self):
        json_log = 'User credentials: {"password": "supersecretpassword123", "token": "xyz987654"}'
        redacted = SensitiveDataFilter.redact(json_log)
        assert "supersecretpassword123" not in redacted
        assert "[REDACTED]" in redacted

    def test_redacts_key_value_secrets(self):
        kv_log = "Connecting with secret=my_db_password_123 and user=admin"
        redacted = SensitiveDataFilter.redact(kv_log)
        assert "my_db_password_123" not in redacted
        assert "secret=[REDACTED]" in redacted

    def test_redacts_pii_email_and_phone(self):
        pii_log = "Candidate contact: candidate.john@example.com, phone: 415-555-2671"
        redacted = SensitiveDataFilter.redact(pii_log)
        assert "candidate.john@example.com" not in redacted
        assert "[REDACTED_EMAIL]" in redacted
        assert "415-555-2671" not in redacted
        assert "[REDACTED_PHONE]" in redacted

    def test_logger_stream_masks_in_actual_output(self):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter("%(message)s"))
        handler.addFilter(SensitiveDataFilter())

        test_logger = logging.getLogger("test_redaction_logger")
        test_logger.setLevel(logging.INFO)
        test_logger.addHandler(handler)
        test_logger.propagate = False

        test_logger.info("Connecting with key=***REMOVED*** and email: user@test.com")
        handler.flush()

        output = stream.getvalue()
        assert "AIzaSy" not in output
        assert "[REDACTED_API_KEY]" in output
        assert "user@test.com" not in output
        assert "[REDACTED_EMAIL]" in output
