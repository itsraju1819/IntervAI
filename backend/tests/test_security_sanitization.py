"""
Unit tests for security sanitization, PDF signature validation, and rate limiting.
"""

import time
from backend.utils.security import RateLimiter, sanitize_text, validate_pdf_signature


class TestTextSanitization:
    """Tests defense mechanisms against XSS, control characters, and DoS payloads."""

    def test_sanitize_empty_and_none(self):
        assert sanitize_text(None) == ""
        assert sanitize_text("") == ""
        assert sanitize_text("   ") == ""

    def test_strips_null_bytes_and_control_chars(self):
        malicious = "Hello\x00World\x08Test\x1FDone"
        sanitized = sanitize_text(malicious)
        assert "\x00" not in sanitized
        assert "\x08" not in sanitized
        assert "\x1F" not in sanitized
        assert "HelloWorldTestDone" in sanitized

    def test_strips_html_tags_and_scripts(self):
        payload = "<script>alert('xss')</script>Normal text<img src=x onerror=alert(1)>"
        sanitized = sanitize_text(payload)
        assert "<script>" not in sanitized
        assert "</script>" not in sanitized
        assert "<img" not in sanitized
        assert "Normal text" in sanitized

    def test_neutralizes_dangerous_uri_schemes(self):
        payload = "javascript:alert(1)"
        sanitized = sanitize_text(payload)
        assert "javascript:" not in sanitized

    def test_html_entity_escaping(self):
        payload = "A & B > C < D 'quote' \"double\""
        sanitized = sanitize_text(payload)
        assert "&amp;" in sanitized
        assert "&gt;" in sanitized
        assert "&lt;" in sanitized
        assert "&quot;" in sanitized
        assert "&#x27;" in sanitized

    def test_max_length_truncation(self):
        long_input = "a" * 20000
        sanitized = sanitize_text(long_input, max_length=50)
        assert len(sanitized) == 50


class TestPdfSignatureValidation:
    """Tests defense against MIME-type spoofing and malicious file payloads."""

    def test_valid_pdf_signature(self):
        valid_pdf_bytes = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj"
        assert validate_pdf_signature(valid_pdf_bytes) is True

    def test_invalid_text_or_script_bytes(self):
        fake_pdf = b"<!DOCTYPE html><html><body>Fake PDF</body></html>"
        assert validate_pdf_signature(fake_pdf) is False

    def test_empty_content(self):
        assert validate_pdf_signature(b"") is False

    def test_oversized_payload_rejected(self):
        # Header is valid PDF, but payload exceeds limit (set small limit for test)
        pdf_chunk = b"%PDF-1.4" + (b"0" * 1000)
        assert validate_pdf_signature(pdf_chunk, max_bytes=500) is False


class TestRateLimiter:
    """Tests sliding window rate limiting."""

    def test_rate_limiter_allows_under_limit(self):
        limiter = RateLimiter(requests_per_window=3, window_seconds=10)
        client_ip = "192.168.1.100"

        allowed1, _ = limiter.is_allowed(client_ip)
        allowed2, _ = limiter.is_allowed(client_ip)
        allowed3, _ = limiter.is_allowed(client_ip)

        assert allowed1 is True
        assert allowed2 is True
        assert allowed3 is True

    def test_rate_limiter_blocks_exceeding_requests(self):
        limiter = RateLimiter(requests_per_window=2, window_seconds=5)
        client_ip = "192.168.1.101"

        limiter.is_allowed(client_ip)
        limiter.is_allowed(client_ip)
        allowed, retry_after = limiter.is_allowed(client_ip)

        assert allowed is False
        assert retry_after > 0

    def test_rate_limiter_window_resets(self):
        limiter = RateLimiter(requests_per_window=1, window_seconds=1)
        client_ip = "192.168.1.102"

        allowed1, _ = limiter.is_allowed(client_ip)
        assert allowed1 is True

        allowed2, _ = limiter.is_allowed(client_ip)
        assert allowed2 is False

        time.sleep(1.05)

        allowed3, _ = limiter.is_allowed(client_ip)
        assert allowed3 is True
