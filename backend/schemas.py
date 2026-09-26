"""
Pydantic schemas for the IntervAI API endpoints.
"""

from typing import Any
from pydantic import BaseModel, Field


class QuestionOut(BaseModel):
    question: str
    topic: str
    question_type: str
    tip: str
    hint: str | None = None
    sample_keywords: list[str] | None = None


class InterviewStartRequest(BaseModel):
    track: str = Field(..., description='"hr_behavioral" or "technical"')
    role_id: str | None = Field(
        default=None,
        description="Required when track is 'technical'. One of roles_config.TECHNICAL_ROLES keys.",
    )
    difficulty: str = Field(..., description='"Beginner", "Intermediate", or "Advanced"')
    resume_summary: str | None = Field(default=None, description="Text summary extracted from resume")
    job_description: str | None = Field(default=None, description="Optional target Job Description text")


class InterviewStartResponse(BaseModel):
    session_id: str
    track: str
    role_id: str | None
    role_name: str
    difficulty: str
    question_number: int
    total_questions: int = 5
    question: QuestionOut
    source: str = Field(
        description='"gemini" if AI-generated, "fallback" if the static bank was used'
    )


class NextQuestionRequest(BaseModel):
    session_id: str
    question_number: int
    last_question: str | None = None
    last_answer: str | None = None
    job_description: str | None = None


class NextQuestionResponse(BaseModel):
    session_id: str
    question_number: int
    total_questions: int = 5
    question: QuestionOut
    source: str


class AnswerItem(BaseModel):
    question: str
    answer: str


class AnswerSubmitRequest(BaseModel):
    session_id: str
    question: str
    answer: str
    question_number: int = 1


class CategoryScores(BaseModel):
    technical_accuracy: int
    clarity_communication: int
    problem_solving: int
    structure: int


class QuestionEvaluation(BaseModel):
    question: str
    score: int
    feedback: str


class InterviewEvaluationRequest(BaseModel):
    session_id: str | None = None
    track: str = "technical"
    role_id: str | None = None
    role_name: str = "Candidate"
    difficulty: str = "Intermediate"
    answers: list[AnswerItem]
    job_description: str | None = None


class InterviewEvaluationResponse(BaseModel):
    overall_score: int
    rating: str
    summary: str
    category_scores: CategoryScores
    strengths: list[str]
    improvements: list[str]
    question_evaluations: list[QuestionEvaluation]
    source: str
    jd_match_score: int | None = None
    matched_keywords: list[str] | None = None
    missing_keywords: list[str] | None = None


class ResumeUploadResponse(BaseModel):
    success: bool
    filename: str
    summary: str
    skills: list[str]


class AnalyzeJdRequest(BaseModel):
    job_description: str
    resume_summary: str | None = None
    resume_skills: list[str] | None = None


class AnalyzeJdResponse(BaseModel):
    has_jd: bool
    jd_skills: list[str]
    match_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    summary: str


class ApiKeyUpdateRequest(BaseModel):
    api_key: str = Field(..., min_length=1)


class ApiKeyUpdateResponse(BaseModel):
    status: str
    message: str
    gemini_configured: bool
