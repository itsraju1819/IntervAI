"""
In-memory interview session store for IntervAI.

Maintains active finite-state-machine (FSM) state for adaptive interview sessions,
including topic progression, follow-up tracking, candidate profiles, and speech metrics.
"""

import uuid
from typing import Any
try:
    from config import settings
except ImportError:
    from backend.config import settings

_sessions: dict[str, dict[str, Any]] = {}


def create_session(
    *,
    track: str,
    role_id: str | None,
    role_name: str,
    difficulty: str,
    resume_summary: str | None = None,
    job_description: str | None = None,
    max_questions: int | None = None,
    expected_topics: list[str] | None = None,
    candidate_profile: dict[str, Any] | None = None,
) -> str:
    session_id = str(uuid.uuid4())
    total_questions = max_questions or settings.DEFAULT_MAX_QUESTIONS
    topics_list = list(expected_topics or [])
    initial_topic = topics_list.pop(0) if topics_list else "Introduction & Core Background"

    _sessions[session_id] = {
        "session_id": session_id,
        "track": track,
        "role_id": role_id,
        "role_name": role_name,
        "difficulty": difficulty,
        "resume_summary": resume_summary,
        "job_description": job_description,
        "candidate_profile": candidate_profile,
        "max_questions": total_questions,
        "question_turn": 1,
        "current_topic": initial_topic,
        "followup_count_for_topic": 0,
        "topics_covered": [],
        "topics_remaining": topics_list,
        "questions_asked": [],   # list of QuestionOut-shaped dicts
        "answers_received": [],  # list of {"question": ..., "answer": ..., "delivery_metrics": ...}
        "intermediate_analyses": [], # list of IntermediateAnswerAnalysis dicts
        "speech_metrics": [],    # list of SpeechDeliveryMetrics dicts
        "status": "in_progress",
        "evaluation": None,
    }
    return session_id


def get_session(session_id: str) -> dict[str, Any] | None:
    return _sessions.get(session_id)


def add_question(session_id: str, question: dict[str, Any]) -> None:
    session = _sessions.get(session_id)
    if session is None:
        raise KeyError(f"Unknown session_id: {session_id}")
    session["questions_asked"].append(question)
    if question.get("topic"):
        session["current_topic"] = question["topic"]


def add_answer(
    session_id: str,
    question: str,
    answer: str,
    delivery_metrics: dict[str, Any] | None = None,
) -> None:
    session = _sessions.get(session_id)
    if session is None:
        raise KeyError(f"Unknown session_id: {session_id}")
    session["answers_received"].append({
        "question": question,
        "answer": answer,
        "delivery_metrics": delivery_metrics,
    })
    if delivery_metrics:
        session["speech_metrics"].append(delivery_metrics)


def record_intermediate_analysis(session_id: str, analysis: dict[str, Any]) -> None:
    session = _sessions.get(session_id)
    if session is not None:
        session["intermediate_analyses"].append(analysis)


def step_followup(session_id: str) -> int:
    """Increments and returns the follow-up counter for the current topic."""
    session = _sessions.get(session_id)
    if session is None:
        raise KeyError(f"Unknown session_id: {session_id}")
    session["followup_count_for_topic"] += 1
    session["question_turn"] += 1
    return session["followup_count_for_topic"]


def step_advance_topic(session_id: str) -> str:
    """
    Appends current topic to topics_covered, pops the next topic from topics_remaining,
    and resets followup_count_for_topic.
    """
    session = _sessions.get(session_id)
    if session is None:
        raise KeyError(f"Unknown session_id: {session_id}")
    if session["current_topic"]:
        session["topics_covered"].append(session["current_topic"])

    if session["topics_remaining"]:
        next_topic = session["topics_remaining"].pop(0)
    else:
        next_topic = "Synthesis & Practical Scenarios"

    session["current_topic"] = next_topic
    session["followup_count_for_topic"] = 0
    session["question_turn"] += 1
    return next_topic


def set_evaluation(session_id: str, evaluation: dict[str, Any]) -> None:
    session = _sessions.get(session_id)
    if session is not None:
        session["evaluation"] = evaluation
        session["status"] = "completed"
