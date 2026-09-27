"""
Integration tests for FastAPI endpoints, security headers, validation, and session flow.
"""

import io
from fastapi.testclient import TestClient


class TestApiEndpoints:
    """End-to-end endpoint tests for IntervAI backend."""

    def test_health_check_endpoint(self, client: TestClient):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "gemini_configured" in data
        assert "environment" in data

    def test_security_headers_present(self, client: TestClient):
        response = client.get("/api/health")
        headers = response.headers
        assert "content-security-policy" in headers
        assert "default-src 'self'" in headers["content-security-policy"]
        assert headers.get("x-content-type-options") == "nosniff"
        assert headers.get("x-frame-options") == "DENY"
        assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_get_roles_endpoint(self, client: TestClient):
        response = client.get("/api/interview/roles")
        assert response.status_code == 200
        data = response.json()
        assert "tracks" in data
        assert "technical_roles" in data
        assert "technical" in data["tracks"]

    def test_start_interview_validation_error_on_bad_track(self, client: TestClient):
        payload = {
            "track": "non_existent_track",
            "difficulty": "Intermediate",
            "max_questions": 5,
        }
        response = client.post("/api/interview/start", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert data.get("error") is True
        assert "detail" in data

    def test_start_interview_validation_error_on_missing_role_for_technical(self, client: TestClient):
        payload = {
            "track": "technical",
            "difficulty": "Intermediate",
            "max_questions": 5,
        }
        response = client.post("/api/interview/start", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert data.get("error") is True

    def test_start_interview_success(self, client: TestClient):
        payload = {
            "track": "technical",
            "role_id": "full_stack_developer",
            "difficulty": "Intermediate",
            "max_questions": 3,
        }
        response = client.post("/api/interview/start", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["question_number"] == 1
        assert data["total_questions"] == 3
        assert "question" in data
        assert "question" in data["question"]
        assert len(data["question"]["question"]) > 0

    def test_upload_resume_rejects_non_pdf_file(self, client: TestClient):
        files = {
            "file": ("malicious.exe", io.BytesIO(b"MZ\x90\x00\x03"), "application/octet-stream"),
        }
        response = client.post("/api/interview/upload-resume", files=files)
        assert response.status_code == 400
        data = response.json()
        assert data.get("error") is True

    def test_upload_resume_rejects_spoofed_pdf_signature(self, client: TestClient):
        # Filename has .pdf extension, but magic bytes are HTML
        fake_content = b"<html><body>Not a real PDF</body></html>"
        files = {
            "file": ("resume.pdf", io.BytesIO(fake_content), "application/pdf"),
        }
        response = client.post("/api/interview/upload-resume", files=files)
        assert response.status_code == 400
        data = response.json()
        assert data.get("error") is True

    def test_get_session_results_not_found(self, client: TestClient):
        response = client.get("/api/interview/results/non-existent-session-id")
        assert response.status_code == 404
        data = response.json()
        assert data.get("error") is True
        assert "detail" in data

    def test_full_interview_turn_flow(self, client: TestClient):
        # 1. Start interview
        start_payload = {
            "track": "hr_behavioral",
            "difficulty": "Intermediate",
            "max_questions": 3,
        }
        start_resp = client.post("/api/interview/start", json=start_payload)
        assert start_resp.status_code == 200
        session_id = start_resp.json()["session_id"]
        q1_text = start_resp.json()["question"]["question"]

        # 2. Next question with candidate answer
        next_payload = {
            "session_id": session_id,
            "question_number": 2,
            "last_question": q1_text,
            "last_answer": "I led a cross-functional squad of 5 engineers to deliver a high-throughput streaming pipeline.",
            "delivery_metrics": {
                "wpm": 140.0,
                "filler_count": 1,
                "clarity_score": "Optimal",
            },
        }
        next_resp = client.post("/api/interview/next-question", json=next_payload)
        assert next_resp.status_code == 200
        next_data = next_resp.json()
        assert next_data["question_number"] == 2
        assert "question" in next_data

        # 3. Check session store has recorded answers and questions
        results_resp = client.get(f"/api/interview/results/{session_id}")
        assert results_resp.status_code == 200
        results_data = results_resp.json()
        assert len(results_data["answers_received"]) >= 1
