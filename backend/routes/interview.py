"""
/api/interview/* routing layer for IntervAI.

This module acts as a strict HTTP routing layer, delegating all business
orchestration, validation, rate limiting, and AI interactions to InterviewController.
"""

from typing import Any
from fastapi import APIRouter, File, Request, UploadFile

try:
    from controllers.interview_controller import InterviewController
    from models.schemas import (
        AnalyzeJdRequest,
        AnalyzeJdResponse,
        AnswerSubmitRequest,
        InterviewEvaluationRequest,
        InterviewEvaluationResponse,
        InterviewStartRequest,
        InterviewStartResponse,
        NextQuestionRequest,
        NextQuestionResponse,
        ResumeUploadResponse,
    )
except ImportError:
    from backend.controllers.interview_controller import InterviewController
    from backend.models.schemas import (
        AnalyzeJdRequest,
        AnalyzeJdResponse,
        AnswerSubmitRequest,
        InterviewEvaluationRequest,
        InterviewEvaluationResponse,
        InterviewStartRequest,
        InterviewStartResponse,
        NextQuestionRequest,
        NextQuestionResponse,
        ResumeUploadResponse,
    )

router = APIRouter(prefix="/api/interview", tags=["interview"])


@router.get("/roles")
def get_roles() -> dict[str, Any]:
    """Allows the frontend to query available tracks and role taxonomies."""
    return InterviewController.get_roles()


@router.post("/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(request: Request, file: UploadFile = File(...)) -> ResumeUploadResponse:
    """Parses an uploaded PDF resume, enforcing magic-byte signature validation and rate limits."""
    return await InterviewController.upload_resume(request, file)


@router.post("/analyze-jd", response_model=AnalyzeJdResponse)
def analyze_job_description(request: Request, payload: AnalyzeJdRequest) -> AnalyzeJdResponse:
    """Analyzes a job description and extracts competencies matched against resume data."""
    return InterviewController.analyze_job_description(request, payload)


@router.post("/start", response_model=InterviewStartResponse)
def start_interview(request: Request, payload: InterviewStartRequest) -> InterviewStartResponse:
    """Starts a new interview session and initializes FSM state tracking."""
    return InterviewController.start_interview(request, payload)


@router.post("/next-question", response_model=NextQuestionResponse)
def get_next_question(request: Request, payload: NextQuestionRequest) -> NextQuestionResponse:
    """
    Evaluates intermediate answer quality, enforces server-side anti-loop caps (max 2 follow-ups),
    and generates the next cross-examination or topic-advancement question.
    """
    return InterviewController.get_next_question(request, payload)


@router.post("/answer")
def submit_answer(request: Request, payload: AnswerSubmitRequest) -> dict[str, Any]:
    """Records candidate response and speech delivery metrics into session state."""
    return InterviewController.submit_answer(request, payload)


@router.post("/evaluate", response_model=InterviewEvaluationResponse)
def evaluate_candidate(request: Request, payload: InterviewEvaluationRequest) -> InterviewEvaluationResponse:
    """Generates comprehensive multi-metric interview evaluation and model rewrites."""
    return InterviewController.evaluate_candidate(request, payload)


@router.get("/results/{session_id}")
def get_session_results(session_id: str) -> dict[str, Any]:
    """Retrieves scorecard and analytics for an interview session."""
    return InterviewController.get_session_results(session_id)
