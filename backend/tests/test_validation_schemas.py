"""
Unit tests for Pydantic input validation models and schema constraints.
"""

import pytest
from pydantic import ValidationError
from backend.models.schemas import (
    AnswerSubmitRequest,
    DeliveryMetrics,
    IntermediateAnswerAnalysis,
    InterviewStartRequest,
)


class TestValidationSchemas:
    """Validates schema constraints, type bounds, and payload sanitization."""

    def test_interview_start_valid_payload(self):
        req = InterviewStartRequest(
            track="technical",
            role_id="full_stack_developer",
            difficulty="Intermediate",
            max_questions=5,
        )
        assert req.track == "technical"
        assert req.role_id == "full_stack_developer"
        assert req.difficulty == "Intermediate"
        assert req.max_questions == 5

    def test_interview_start_invalid_track(self):
        with pytest.raises(ValidationError) as excinfo:
            InterviewStartRequest(track="invalid_track_name")
        assert "track" in str(excinfo.value)

    def test_interview_start_invalid_difficulty(self):
        with pytest.raises(ValidationError) as excinfo:
            InterviewStartRequest(
                track="hr_behavioral",
                difficulty="ExtremeMaster",
            )
        assert "difficulty" in str(excinfo.value)

    def test_interview_start_max_questions_bounds(self):
        # Below min (1)
        with pytest.raises(ValidationError):
            InterviewStartRequest(track="hr_behavioral", max_questions=0)

        # Above max (20)
        with pytest.raises(ValidationError):
            InterviewStartRequest(track="hr_behavioral", max_questions=25)

    def test_answer_submit_sanitizes_html_in_answer(self):
        req = AnswerSubmitRequest(
            session_id="valid-session-12345",
            question="Tell me about your experience.",
            answer="<script>alert('pwned')</script> I built a distributed database.",
        )
        assert "<script>" not in req.answer
        assert "distributed database" in req.answer

    def test_answer_submit_rejects_malicious_session_id(self):
        # SQL Injection attempt in session_id must fail regex validator
        with pytest.raises(ValidationError):
            AnswerSubmitRequest(
                session_id="test'; DROP TABLE sessions;--",
                question="Question",
                answer="Answer",
            )

    def test_delivery_metrics_bounds(self):
        # Valid metrics
        metrics = DeliveryMetrics(wpm=145.5, filler_count=2, clarity_score="High")
        assert metrics.wpm == 145.5
        assert metrics.filler_count == 2

        # Negative WPM rejected
        with pytest.raises(ValidationError):
            DeliveryMetrics(wpm=-10.0)

        # Extreme WPM (>500) rejected
        with pytest.raises(ValidationError):
            DeliveryMetrics(wpm=600.0)

        # Negative filler count rejected
        with pytest.raises(ValidationError):
            DeliveryMetrics(filler_count=-1)

    def test_intermediate_answer_analysis_schema(self):
        analysis = IntermediateAnswerAnalysis(
            relevance_score=8.5,
            depth_score=7.0,
            specificity_score=7.5,
            identified_gaps=["Could discuss concurrency"],
            detected_claims=["Used Redis for caching"],
            decision="DRILL_DOWN",
            reasoning="Strong response with clear opportunity to probe cache invalidation.",
        )
        assert analysis.decision == "DRILL_DOWN"
        assert analysis.relevance_score == 8.5

        # Invalid decision rejected
        with pytest.raises(ValidationError):
            IntermediateAnswerAnalysis(
                relevance_score=8.0,
                depth_score=7.0,
                specificity_score=7.0,
                identified_gaps=[],
                detected_claims=[],
                decision="INVALID_DECISION",
                reasoning="Test",
            )

        # Out-of-bounds score (>10) rejected
        with pytest.raises(ValidationError):
            IntermediateAnswerAnalysis(
                relevance_score=15.0,
                depth_score=7.0,
                specificity_score=7.0,
                identified_gaps=[],
                detected_claims=[],
                decision="ADVANCE_TOPIC",
                reasoning="Test",
            )
