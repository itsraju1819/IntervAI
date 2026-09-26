"""
/api/interview/* routes for IntervAI.

Provides interview session management, resume upload, Job Description analysis,
dynamic question generation with student hints, answer recording, and final evaluation.
"""

import logging
import os
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile

from prompts.interviewer_prompt import (
    INTERVIEWER_SYSTEM_INSTRUCTION,
    QUESTION_RESPONSE_SCHEMA,
    build_next_question_prompt,
    build_opening_question_prompt,
)
from roles_config import TRACKS, get_role_profile, list_technical_roles
from schemas import (
    AnalyzeJdRequest,
    AnalyzeJdResponse,
    ApiKeyUpdateRequest,
    ApiKeyUpdateResponse,
    AnswerSubmitRequest,
    InterviewEvaluationRequest,
    InterviewEvaluationResponse,
    InterviewStartRequest,
    InterviewStartResponse,
    NextQuestionRequest,
    NextQuestionResponse,
    QuestionOut,
    ResumeUploadResponse,
)
from services import session_store
from services.evaluation_service import evaluate_interview
from services.fallback_questions import get_fallback_opening_question, get_fallback_question
from services.gemini_service import GeminiServiceError, gemini_service
from services.jd_service import analyze_jd_and_resume
from services.resume_service import parse_resume

logger = logging.getLogger("intervai.interview")

router = APIRouter(prefix="/api/interview", tags=["interview"])


@router.get("/roles")
def get_roles() -> dict:
    """Allows the frontend to build track and role selectors dynamically."""
    return {
        "tracks": TRACKS,
        "technical_roles": list_technical_roles(),
    }


@router.post("/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)) -> ResumeUploadResponse:
    """Parses an uploaded PDF resume, extracting text and key skills."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported.")

    try:
        content = await file.read()
        parsed = parse_resume(content, filename=file.filename)
        return ResumeUploadResponse(**parsed)
    except Exception as exc:
        logger.error("Resume upload processing failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not process uploaded resume.") from exc


@router.post("/analyze-jd", response_model=AnalyzeJdResponse)
def analyze_job_description(payload: AnalyzeJdRequest) -> AnalyzeJdResponse:
    """Analyzes a job description and compares against candidate resume."""
    result = analyze_jd_and_resume(
        payload.job_description,
        resume_text=payload.resume_summary,
        resume_skills=payload.resume_skills,
    )
    return AnalyzeJdResponse(**result)


@router.post("/start", response_model=InterviewStartResponse)
def start_interview(payload: InterviewStartRequest) -> InterviewStartResponse:
    """Starts a new interview session and generates Question 1."""
    if payload.track not in TRACKS:
        raise HTTPException(status_code=400, detail=f"Unknown track: {payload.track!r}")

    if payload.track == "technical" and not payload.role_id:
        raise HTTPException(status_code=400, detail="role_id is required for technical track")

    if payload.difficulty not in ("Beginner", "Intermediate", "Advanced"):
        raise HTTPException(status_code=400, detail=f"Unknown difficulty: {payload.difficulty!r}")

    try:
        role = get_role_profile(payload.track, payload.role_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    source = "gemini"
    question_data: dict

    if gemini_service.is_configured:
        try:
            prompt = build_opening_question_prompt(
                track=payload.track,
                role=role,
                difficulty=payload.difficulty,
                resume_summary=payload.resume_summary,
                job_description=payload.job_description,
            )
            question_data = gemini_service.generate_json(
                prompt,
                QUESTION_RESPONSE_SCHEMA,
                system_instruction=INTERVIEWER_SYSTEM_INSTRUCTION,
            )
        except GeminiServiceError as exc:
            logger.warning("Gemini opening question failed, using fallback: %s", exc)
            question_data = get_fallback_opening_question(payload.track, payload.role_id)
            source = "fallback"
    else:
        logger.info("Gemini not configured, using fallback question bank.")
        question_data = get_fallback_opening_question(payload.track, payload.role_id)
        source = "fallback"

    try:
        question = QuestionOut(**question_data)
    except Exception as exc:
        logger.error("Question validation failed (%s), using fallback.", exc)
        question = QuestionOut(**get_fallback_opening_question(payload.track, payload.role_id))
        source = "fallback"

    session_id = session_store.create_session(
        track=payload.track,
        role_id=payload.role_id,
        role_name=role["role_name"],
        difficulty=payload.difficulty,
        resume_summary=payload.resume_summary,
        job_description=payload.job_description,
    )
    session_store.add_question(session_id, question.model_dump())

    return InterviewStartResponse(
        session_id=session_id,
        track=payload.track,
        role_id=payload.role_id,
        role_name=role["role_name"],
        difficulty=payload.difficulty,
        question_number=1,
        total_questions=5,
        question=question,
        source=source,
    )


@router.post("/next-question", response_model=NextQuestionResponse)
def get_next_question(payload: NextQuestionRequest) -> NextQuestionResponse:
    """
    Generates the next adaptive question in the sequence based on the candidate's
    previous response, resume, and Job Description.
    """
    session = session_store.get_session(payload.session_id)
    if not session:
        fallback_q = get_fallback_question("technical", None, payload.question_number)
        return NextQuestionResponse(
            session_id=payload.session_id,
            question_number=payload.question_number,
            total_questions=5,
            question=QuestionOut(**fallback_q),
            source="fallback",
        )

    # Record previous answer if provided
    if payload.last_question and payload.last_answer:
        session_store.add_answer(payload.session_id, payload.last_question, payload.last_answer)

    track = session["track"]
    role_id = session["role_id"]
    difficulty = session["difficulty"]
    resume_summary = session.get("resume_summary")
    job_description = payload.job_description or session.get("job_description")
    qa_history = session.get("answers_received", [])

    role = get_role_profile(track, role_id)
    source = "gemini"
    question_data: dict

    if gemini_service.is_configured:
        try:
            prompt = build_next_question_prompt(
                track=track,
                role=role,
                difficulty=difficulty,
                question_number=payload.question_number,
                total_questions=5,
                qa_history=qa_history,
                resume_summary=resume_summary,
                job_description=job_description,
            )
            question_data = gemini_service.generate_json(
                prompt,
                QUESTION_RESPONSE_SCHEMA,
                system_instruction=INTERVIEWER_SYSTEM_INSTRUCTION,
            )
        except GeminiServiceError as exc:
            logger.warning("Adaptive question generation failed, using fallback: %s", exc)
            question_data = get_fallback_question(track, role_id, payload.question_number)
            source = "fallback"
    else:
        question_data = get_fallback_question(track, role_id, payload.question_number)
        source = "fallback"

    try:
        question = QuestionOut(**question_data)
    except Exception as exc:
        logger.error("Next question validation failed (%s), using fallback.", exc)
        question = QuestionOut(**get_fallback_question(track, role_id, payload.question_number))
        source = "fallback"

    session_store.add_question(payload.session_id, question.model_dump())

    return NextQuestionResponse(
        session_id=payload.session_id,
        question_number=payload.question_number,
        total_questions=5,
        question=question,
        source=source,
    )


@router.post("/answer")
def submit_answer(payload: AnswerSubmitRequest) -> dict:
    """Records a candidate's answer into the active session."""
    session = session_store.get_session(payload.session_id)
    if session is None:
        logger.warning("Session %s not found in memory", payload.session_id)
        return {"status": "recorded_stateless", "session_id": payload.session_id}

    session_store.add_answer(payload.session_id, payload.question, payload.answer)
    return {"status": "ok", "answers_count": len(session["answers_received"])}


@router.post("/evaluate", response_model=InterviewEvaluationResponse)
def evaluate_candidate(payload: InterviewEvaluationRequest) -> InterviewEvaluationResponse:
    """Evaluates the full set of answers and returns score and detailed feedback."""
    qa_list = [qa.model_dump() for qa in payload.answers]
    session = session_store.get_session(payload.session_id) if payload.session_id else None
    jd = payload.job_description or (session.get("job_description") if session else None)

    result = evaluate_interview(
        track=payload.track,
        role_name=payload.role_name,
        difficulty=payload.difficulty,
        qa_list=qa_list,
        job_description=jd,
    )

    if payload.session_id:
        session_store.set_evaluation(payload.session_id, result)

    return InterviewEvaluationResponse(**result)


@router.get("/results/{session_id}")
def get_session_results(session_id: str) -> dict:
    """Fetch stored results for an interview session."""
    session = session_store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    return session


@router.post("/config/key", response_model=ApiKeyUpdateResponse)
def update_api_key(payload: ApiKeyUpdateRequest) -> ApiKeyUpdateResponse:
    """Updates the Gemini API key dynamically and saves to .env."""
    clean_key = payload.api_key.strip()
    if not clean_key:
        raise HTTPException(status_code=400, detail="API key cannot be empty.")

    os.environ["GEMINI_API_KEY"] = clean_key

    env_path = Path(__file__).resolve().parent.parent / ".env"
    try:
        lines = []
        key_found = False
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("GEMINI_API_KEY="):
                    lines.append(f"GEMINI_API_KEY={clean_key}")
                    key_found = True
                else:
                    lines.append(line)
        if not key_found:
            lines.insert(0, f"GEMINI_API_KEY={clean_key}")

        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception as exc:
        logger.warning("Could not persist key to .env file: %s", exc)

    test_ok = gemini_service.is_configured
    return ApiKeyUpdateResponse(
        status="ok",
        message="Gemini API key updated successfully." if test_ok else "Key updated, verifying client...",
        gemini_configured=test_ok,
    )
