"""
Pydantic schemas for the IntervAI API endpoints.
Defines models for interview sessions, adaptive FSM tracking, candidate profiles,
speech analytics, and STAR answer rewrites.
"""

from typing import Any
from pydantic import BaseModel, Field


class ProjectItem(BaseModel):
    project_name: str
    claimed_metrics: list[str] = Field(default_factory=list)
    core_technologies: list[str] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    technical_stack: list[str] = Field(default_factory=list)
    key_projects: list[ProjectItem] = Field(default_factory=list)
    experience_level: str = "Mid-Level"


class SpeechDeliveryMetrics(BaseModel):
    duration_seconds: float = 0.0
    total_words: int = 0
    wpm: float = 0.0
    filler_count: int = 0
    filler_words_detected: list[str] = Field(default_factory=list)


class IntermediateAnswerAnalysis(BaseModel):
    relevance_score: float = Field(..., ge=0.0, le=10.0, description="Relevance of answer (0-10)")
    depth_score: float = Field(..., ge=0.0, le=10.0, description="Technical/behavioral depth (0-10)")
    specificity_score: float = Field(..., ge=0.0, le=10.0, description="Specificity and metric precision (0-10)")
    identified_gaps: list[str] = Field(default_factory=list, description="Unaddressed parts of the question or technical inaccuracies")
    detected_claims: list[str] = Field(default_factory=list, description="Metrics, architectural claims, or tools candidate mentioned")
    decision: str = Field(..., description="Deterministic decision: DRILL_DOWN | ADVANCE_TOPIC | WRAP_UP")
    reasoning: str = Field(..., description="Justification for the decision")


class StarBreakdown(BaseModel):
    situation: bool = False
    task: bool = False
    action: bool = False
    result: bool = False
    feedback: str = ""


class AnswerRewrite(BaseModel):
    question: str
    original_answer: str
    critique: str
    rewritten_answer: str
    star_alignment: StarBreakdown | None = None


class QuestionOut(BaseModel):
    question: str
    topic: str
    question_type: str
    tip: str
    hint: str | None = None
    sample_keywords: list[str] | None = None
    targeted_metric_or_project: str | None = None


class InterviewStartRequest(BaseModel):
    track: str = Field(..., description='"hr_behavioral" or "technical"')
    role_id: str | None = Field(
        default=None,
        description="Required when track is 'technical'. One of roles_config.TECHNICAL_ROLES keys.",
    )
    difficulty: str = Field(..., description='"Beginner", "Intermediate", or "Advanced"')
    resume_summary: str | None = Field(default=None, description="Text summary extracted from resume")
    job_description: str | None = Field(default=None, description="Optional target Job Description text")
    max_questions: int | None = Field(default=None, description="Optional total questions cap (defaults to config)")
    candidate_profile: CandidateProfile | None = Field(default=None, description="Structured profile parsed from resume")


class InterviewStartResponse(BaseModel):
    session_id: str
    track: str
    role_id: str | None
    role_name: str
    difficulty: str
    question_number: int
    total_questions: int
    current_topic: str | None = None
    topics_remaining: list[str] = Field(default_factory=list)
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
    delivery_metrics: SpeechDeliveryMetrics | None = None


class NextQuestionResponse(BaseModel):
    session_id: str
    question_number: int
    total_questions: int
    question: QuestionOut
    source: str
    analysis: IntermediateAnswerAnalysis | None = None
    current_topic: str | None = None
    followup_count: int = 0
    is_followup: bool = False
    topics_covered: list[str] = Field(default_factory=list)
    topics_remaining: list[str] = Field(default_factory=list)
    is_final_question: bool = False


class AnswerItem(BaseModel):
    question: str
    answer: str
    delivery_metrics: SpeechDeliveryMetrics | None = None


class AnswerSubmitRequest(BaseModel):
    session_id: str
    question: str
    answer: str
    question_number: int = 1
    delivery_metrics: SpeechDeliveryMetrics | None = None


class CategoryScores(BaseModel):
    technical_accuracy: int
    clarity_communication: int
    problem_solving: int
    structure: int


class QuestionEvaluation(BaseModel):
    question: str
    score: int
    feedback: str
    delivery_metrics: SpeechDeliveryMetrics | None = None


class InterviewEvaluationRequest(BaseModel):
    session_id: str | None = None
    track: str = "technical"
    role_id: str | None = None
    role_name: str = "Candidate"
    difficulty: str = "Intermediate"
    answers: list[AnswerItem]
    job_description: str | None = None
    speech_metrics: list[SpeechDeliveryMetrics] | None = None


class InterviewEvaluationResponse(BaseModel):
    overall_score: int
    rating: str
    summary: str
    category_scores: CategoryScores
    strengths: list[str]
    improvements: list[str]
    question_evaluations: list[QuestionEvaluation]
    source: str
    is_fallback: bool = False
    evaluation_status: str = "completed"
    message: str | None = None
    jd_match_score: int | None = None
    matched_keywords: list[str] | None = None
    missing_keywords: list[str] | None = None
    star_breakdown: StarBreakdown | None = None
    weakest_answer_rewrite: AnswerRewrite | None = None
    average_wpm: float | None = None
    total_filler_words: int | None = None
    speech_delivery_summary: str | None = None


class ResumeUploadResponse(BaseModel):
    success: bool
    filename: str
    summary: str
    skills: list[str]
    candidate_profile: CandidateProfile | None = None


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
