"""
Backwards-compatible export layer for IntervAI schemas.
Exports all models directly from backend.models.schemas.
"""

try:
    from models.schemas import (
        AnalyzeJdRequest,
        AnalyzeJdResponse,
        AnswerSubmitRequest,
        CandidateProfile,
        CategoryScores,
        DeliveryMetrics,
        IntermediateAnswerAnalysis,
        InterviewEvaluationRequest,
        InterviewEvaluationResponse,
        InterviewStartRequest,
        InterviewStartResponse,
        ModelAnswerRewrite,
        NextQuestionRequest,
        NextQuestionResponse,
        ProjectItem,
        QaEvaluationItem,
        QuestionOut,
        ResumeUploadResponse,
        SpeechDeliveryMetrics,
        StarBreakdown,
    )
except ImportError:
    from backend.models.schemas import (
        AnalyzeJdRequest,
        AnalyzeJdResponse,
        AnswerSubmitRequest,
        CandidateProfile,
        CategoryScores,
        DeliveryMetrics,
        IntermediateAnswerAnalysis,
        InterviewEvaluationRequest,
        InterviewEvaluationResponse,
        InterviewStartRequest,
        InterviewStartResponse,
        ModelAnswerRewrite,
        NextQuestionRequest,
        NextQuestionResponse,
        ProjectItem,
        QaEvaluationItem,
        QuestionOut,
        ResumeUploadResponse,
        SpeechDeliveryMetrics,
        StarBreakdown,
    )

__all__ = [
    "AnalyzeJdRequest",
    "AnalyzeJdResponse",
    "AnswerSubmitRequest",
    "CandidateProfile",
    "CategoryScores",
    "DeliveryMetrics",
    "IntermediateAnswerAnalysis",
    "InterviewEvaluationRequest",
    "InterviewEvaluationResponse",
    "InterviewStartRequest",
    "InterviewStartResponse",
    "ModelAnswerRewrite",
    "NextQuestionRequest",
    "NextQuestionResponse",
    "ProjectItem",
    "QaEvaluationItem",
    "QuestionOut",
    "ResumeUploadResponse",
    "SpeechDeliveryMetrics",
    "StarBreakdown",
]
