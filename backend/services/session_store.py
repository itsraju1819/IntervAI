"""
In-memory interview session store.

Maintains state for the currently active interview sessions.
"""

import uuid
from typing import Any

_sessions: dict[str, dict[str, Any]] = {}


def create_session(
    *,
    track: str,
    role_id: str | None,
    role_name: str,
    difficulty: str,
    resume_summary: str | None = None,
    job_description: str | None = None,
) -> str:
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "session_id": session_id,
        "track": track,
        "role_id": role_id,
        "role_name": role_name,
        "difficulty": difficulty,
        "resume_summary": resume_summary,
        "job_description": job_description,
        "questions_asked": [],   # list of QuestionOut-shaped dicts, in order
        "answers_received": [],  # list of {"question": ..., "answer": ...}
        "current_topic": None,
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
    session["current_topic"] = question.get("topic")


def add_answer(session_id: str, question: str, answer: str) -> None:
    session = _sessions.get(session_id)
    if session is None:
        raise KeyError(f"Unknown session_id: {session_id}")
    session["answers_received"].append({"question": question, "answer": answer})


def set_evaluation(session_id: str, evaluation: dict[str, Any]) -> None:
    session = _sessions.get(session_id)
    if session is not None:
        session["evaluation"] = evaluation
        session["status"] = "completed"
