"""
Pydantic domain models and schemas for IntervAI.

Enforces strict input validation, length bounds, regex constraints, and data sanitization
to eliminate injection, XSS, and payload overflow vulnerabilities.
"""

import re
from pydantic import BaseModel, Field, field_validator

try:
    from utils.security import sanitize_text
except ImportError:
    from backend.utils.security import sanitize_text

# Regex for UUID or safe alphanumeric session identifiers
SESSION_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{4,64}$")
TRACK_REGEX = re.compile(r"^(technical|hr_behavioral)$")
DIFFICULTY_REGEX = re.compile(r"^(Beginner|Intermediate|Advanced)$")


class ProjectItem(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=200)
    claimed_metrics: list[str] = Field(default_factory=list)
    core_technologies: list[str] = Field(default_factory=list)

    @field_validator("project_name")
    @classmethod
    def sanitize_project_name(cls, v: str) -> str:
        return sanitize_text(v, max_length=200)

    @field_validator("claimed_metrics", "core_technologies")
    @classmethod
    def sanitize_lists(cls, v: list[str]) -> list[str]:
        return [sanitize_text(item, max_length=150) for item in v[:20] if item]


class CandidateProfile(BaseModel):
    technical_stack: list[str] = Field(default_factory=list)
    key_projects: list[ProjectItem] = Field(default_factory=list)
    experience_level: str = Field(default="Mid-Level", max_length=50)

    @field_validator("experience_level")
    @classmethod
    def sanitize_experience(cls, v: str) -> str:
        return sanitize_text(v, max_length=50)

    @field_validator("technical_stack")
    @classmethod
    def sanitize_stack(cls, v: list[str]) -> list[str]:
        return [sanitize_text(item, max_length=60) for item in v[:50] if item]


class SpeechDeliveryMetrics(BaseModel):
    duration_seconds: float = Field(default=0.0, ge=0.0, le=3600.0)
    total_words: int = Field(default=0, ge=0, le=10000)
    wpm: float = Field(default=0.0, ge=0.0, le=350.0)
    filler_count: int = Field(default=0, ge=0, le=500)
    filler_words_detected: list[str] = Field(default_factory=list)


# Alias for backwards compatibility and clean naming
DeliveryMetrics = SpeechDeliveryMetrics


class IntermediateAnswerAnalysis(BaseModel):
    relevance_score: float = Field(..., ge=0.0, le=10.0, description="Relevance of answer (0-10)")
    depth_score: float = Field(..., ge=0.0, le=10.0, description="Technical/behavioral depth (0-10)")
    specificity_score: float = Field(..., ge=0.0, le=10.0, description="Specificity and metric precision (0-10)")
    identified_gaps: list[str] = Field(default_factory=list, description="Unaddressed parts of the question")
    detected_claims: list[str] = Field(default_factory=list, description="Metrics or architectural claims detected")
    decision: str = Field(..., pattern="^(DRILL_DOWN|ADVANCE_TOPIC|WRAP_UP)$")
    reasoning: str = Field(..., max_length=2000)


class StarBreakdown(BaseModel):
    situation: bool = False
    task: bool = False
    action: bool = False
    result: bool = False
    feedback: str = Field(default="", max_length=2000)


class AnswerRewrite(BaseModel):
    question: str = Field(..., max_length=1000)
    original_answer: str = Field(..., max_length=10000)
    critique: str = Field(..., max_length=2000)
    rewritten_answer: str = Field(..., max_length=10000)
    star_alignment: StarBreakdown | None = None


class QuestionOut(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    topic: str = Field(..., min_length=1, max_length=200)
    question_type: str = Field(..., max_length=100)
    tip: str = Field(..., max_length=500)
    hint: str | None = Field(default=None, max_length=2000)
    sample_keywords: list[str] | None = None
    targeted_metric_or_project: str | None = Field(default=None, max_length=200)


class InterviewStartRequest(BaseModel):
    track: str = Field(..., pattern="^(technical|hr_behavioral)$", description='"hr_behavioral" or "technical"')
    role_id: str | None = Field(
        default=None,
        max_length=100,
        description="Required when track is 'technical'. One of roles_config.TECHNICAL_ROLES keys.",
    )
    difficulty: str = Field(..., pattern="^(Beginner|Intermediate|Advanced)$", description='"Beginner", "Intermediate", or "Advanced"')
    resume_summary: str | None = Field(default=None, max_length=15000, description="Text summary extracted from resume")
    job_description: str | None = Field(default=None, max_length=15000, description="Optional target Job Description text")
    max_questions: int | None = Field(default=None, ge=3, le=20, description="Optional total questions cap (3 to 20)")
    candidate_profile: CandidateProfile | None = Field(default=None, description="Structured profile parsed from resume")

    @field_validator("resume_summary", "job_description")
    @classmethod
    def sanitize_long_texts(cls, v: str | None) -> str | None:
        return sanitize_text(v, max_length=15000) if v else None


class InterviewStartResponse(BaseModel):
    session_id: str = Field(..., pattern="^[a-zA-Z0-9_\\-]{4,64}$")
    track: str
    role_id: str | None
    role_name: str
    difficulty: str
    question_number: int = Field(..., ge=1, le=50)
    total_questions: int = Field(..., ge=1, le=50)
    current_topic: str | None = None
    topics_remaining: list[str] = Field(default_factory=list)
    question: QuestionOut
    source: str = Field(description='"gemini" or "fallback"')


class NextQuestionRequest(BaseModel):
    session_id: str = Field(..., pattern="^[a-zA-Z0-9_\\-]{4,64}$")
    question_number: int = Field(..., ge=1, le=50)
    last_question: str | None = Field(default=None, max_length=2000)
    last_answer: str | None = Field(default=None, max_length=15000)
    job_description: str | None = Field(default=None, max_length=15000)
    delivery_metrics: SpeechDeliveryMetrics | None = None

    @field_validator("last_question")
    @classmethod
    def sanitize_question(cls, v: str | None) -> str | None:
        return sanitize_text(v, max_length=2000) if v else None

    @field_validator("last_answer", "job_description")
    @classmethod
    def sanitize_answer(cls, v: str | None) -> str | None:
        return sanitize_text(v, max_length=15000) if v else None


class NextQuestionResponse(BaseModel):
    session_id: str
    question_number: int
    total_questions: int
    question: QuestionOut
    source: str
    analysis: IntermediateAnswerAnalysis | None = None
    current_topic: str | None = None
    followup_count: int = Field(default=0, ge=0, le=10)
    is_followup: bool = False
    topics_covered: list[str] = Field(default_factory=list)
    topics_remaining: list[str] = Field(default_factory=list)
    is_final_question: bool = False


class AnswerItem(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    answer: str = Field(..., max_length=15000)
    delivery_metrics: SpeechDeliveryMetrics | None = None

    @field_validator("question")
    @classmethod
    def sanitize_q(cls, v: str) -> str:
        return sanitize_text(v, max_length=2000)

    @field_validator("answer")
    @classmethod
    def sanitize_a(cls, v: str) -> str:
        return sanitize_text(v, max_length=15000)


class AnswerSubmitRequest(BaseModel):
    session_id: str = Field(..., pattern="^[a-zA-Z0-9_\\-]{4,64}$")
    question: str = Field(..., min_length=1, max_length=2000)
    answer: str = Field(..., max_length=15000)
    question_number: int = Field(default=1, ge=1, le=50)
    delivery_metrics: SpeechDeliveryMetrics | None = None

    @field_validator("question")
    @classmethod
    def sanitize_q(cls, v: str) -> str:
        return sanitize_text(v, max_length=2000)

    @field_validator("answer")
    @classmethod
    def sanitize_a(cls, v: str) -> str:
        return sanitize_text(v, max_length=15000)


class CategoryScores(BaseModel):
    technical_accuracy: int = Field(..., ge=0, le=100)
    clarity_communication: int = Field(..., ge=0, le=100)
    problem_solving: int = Field(..., ge=0, le=100)
    structure: int = Field(..., ge=0, le=100)


class QuestionEvaluation(BaseModel):
    question: str
    score: int = Field(..., ge=0, le=100)
    feedback: str
    delivery_metrics: SpeechDeliveryMetrics | None = None


class InterviewEvaluationRequest(BaseModel):
    session_id: str | None = Field(default=None, pattern="^[a-zA-Z0-9_\\-]{4,64}$")
    track: str = Field(default="technical", pattern="^(technical|hr_behavioral)$")
    role_id: str | None = Field(default=None, max_length=100)
    role_name: str = Field(default="Candidate", max_length=100)
    difficulty: str = Field(default="Intermediate", pattern="^(Beginner|Intermediate|Advanced)$")
    answers: list[AnswerItem] = Field(..., min_length=1, max_length=50)
    job_description: str | None = Field(default=None, max_length=15000)
    speech_metrics: list[SpeechDeliveryMetrics] | None = None


class InterviewEvaluationResponse(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    rating: str = Field(..., max_length=50)
    summary: str
    category_scores: CategoryScores
    strengths: list[str]
    improvements: list[str]
    question_evaluations: list[QuestionEvaluation]
    source: str
    is_fallback: bool = False
    evaluation_status: str = "completed"
    message: str | None = None
    jd_match_score: int | None = Field(default=None, ge=0, le=100)
    matched_keywords: list[str] | None = None
    missing_keywords: list[str] | None = None
    star_breakdown: StarBreakdown | None = None
    weakest_answer_rewrite: AnswerRewrite | None = None
    average_wpm: float | None = None
    total_filler_words: int | None = None
    speech_delivery_summary: str | None = None


class ResumeUploadResponse(BaseModel):
    success: bool
    filename: str = Field(..., max_length=255)
    summary: str
    skills: list[str]
    candidate_profile: CandidateProfile | None = None


class AnalyzeJdRequest(BaseModel):
    job_description: str = Field(..., min_length=1, max_length=15000)
    resume_summary: str | None = Field(default=None, max_length=15000)
    resume_skills: list[str] | None = None

    @field_validator("job_description", "resume_summary")
    @classmethod
    def sanitize_jd_text(cls, v: str | None) -> str | None:
        return sanitize_text(v, max_length=15000) if v else None


class AnalyzeJdResponse(BaseModel):
    has_jd: bool
    jd_skills: list[str]
    match_score: int = Field(..., ge=0, le=100)
    matched_skills: list[str]
    missing_skills: list[str]
    summary: str
