"""
/api/interview/* routes for IntervAI.

Provides state-aware finite-state-machine (FSM) interview management,
deep resume ingestion, intermediate answer evaluation with anti-loop topic transitions,
and final multi-metric scoring with STAR breakdowns and model answer rewrites.
"""

import logging
from typing import Any
from fastapi import APIRouter, File, HTTPException, UploadFile

from config import settings
from prompts.interviewer_prompt import (
    INTERMEDIATE_EVALUATION_SCHEMA,
    INTERVIEWER_SYSTEM_INSTRUCTION,
    QUESTION_RESPONSE_SCHEMA,
    build_advance_question_prompt,
    build_drilldown_question_prompt,
    build_intermediate_analysis_prompt,
    build_opening_question_prompt,
)
from roles_config import TRACKS, get_role_profile, list_technical_roles
from schemas import (
    AnalyzeJdRequest,
    AnalyzeJdResponse,
    AnswerSubmitRequest,
    CandidateProfile,
    IntermediateAnswerAnalysis,
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


def _heuristic_intermediate_analysis(
    question: str,
    answer: str,
    followup_count: int,
) -> dict[str, Any]:
    """Fallback deterministic intermediate analysis when AI service is offline."""
    words = answer.split()
    word_count = len(words)

    if word_count < 20:
        relevance = 5.0
        depth = 3.5
        specificity = 3.0
        gaps = ["Answer was very concise; lacked technical detail and methodology."]
        claims = []
        decision = "DRILL_DOWN" if followup_count < 2 else "ADVANCE_TOPIC"
        reasoning = "Brief answer requires cross-examination to assess candidate depth."
    else:
        relevance = 8.0
        depth = 7.5
        specificity = 7.0
        gaps = ["Could further articulate edge cases and failure modes."]
        claims = ["Stated practical project experience and design reasoning."]
        decision = "DRILL_DOWN" if followup_count < 1 else "ADVANCE_TOPIC"
        reasoning = "Answer demonstrated baseline competence; ready for targeted probing or topic advancement."

    return {
        "relevance_score": relevance,
        "depth_score": depth,
        "specificity_score": specificity,
        "identified_gaps": gaps,
        "detected_claims": claims,
        "decision": decision,
        "reasoning": reasoning,
    }


@router.get("/roles")
def get_roles() -> dict:
    """Allows the frontend to build track and role selectors dynamically."""
    return {
        "tracks": TRACKS,
        "technical_roles": list_technical_roles(),
    }


@router.post("/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)) -> ResumeUploadResponse:
    """Parses an uploaded PDF resume using pdfplumber + Gemini structured output."""
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
    """Starts a new interview session and initializes FSM state machine tracking."""
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

    total_questions = payload.max_questions or settings.DEFAULT_MAX_QUESTIONS
    expected_topics = list(role.get("expected_topics", ["Core Fundamentals"]))
    candidate_profile_dict = payload.candidate_profile.model_dump() if payload.candidate_profile else None

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
                candidate_profile=candidate_profile_dict,
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
        max_questions=total_questions,
        expected_topics=expected_topics,
        candidate_profile=candidate_profile_dict,
    )
    session_store.add_question(session_id, question.model_dump())

    session = session_store.get_session(session_id)
    current_topic = session.get("current_topic") if session else question.topic
    topics_remaining = session.get("topics_remaining", []) if session else []

    return InterviewStartResponse(
        session_id=session_id,
        track=payload.track,
        role_id=payload.role_id,
        role_name=role["role_name"],
        difficulty=payload.difficulty,
        question_number=1,
        total_questions=total_questions,
        current_topic=current_topic,
        topics_remaining=topics_remaining,
        question=question,
        source=source,
    )


@router.post("/next-question", response_model=NextQuestionResponse)
def get_next_question(payload: NextQuestionRequest) -> NextQuestionResponse:
    """
    Executes an intermediate structured evaluation of the candidate's last answer,
    applies server-side deterministic anti-loop rules (max 2 follow-ups per topic),
    and generates either a cross-examination question or advances to a fresh topic.
    """
    session = session_store.get_session(payload.session_id)
    if not session:
        fallback_q = get_fallback_question("technical", None, payload.question_number)
        return NextQuestionResponse(
            session_id=payload.session_id,
            question_number=payload.question_number,
            total_questions=settings.DEFAULT_MAX_QUESTIONS,
            question=QuestionOut(**fallback_q),
            source="fallback",
            current_topic=fallback_q.get("topic"),
            topics_covered=[],
            topics_remaining=[],
            is_final_question=payload.question_number >= settings.DEFAULT_MAX_QUESTIONS,
        )

    # 1. Record previous answer and speech delivery metrics
    delivery_metrics_dict = payload.delivery_metrics.model_dump() if payload.delivery_metrics else None
    if payload.last_question and payload.last_answer:
        session_store.add_answer(
            payload.session_id,
            payload.last_question,
            payload.last_answer,
            delivery_metrics=delivery_metrics_dict,
        )

    track = session["track"]
    role_id = session["role_id"]
    difficulty = session["difficulty"]
    resume_summary = session.get("resume_summary")
    candidate_profile = session.get("candidate_profile")
    job_description = payload.job_description or session.get("job_description")
    qa_history = session.get("answers_received", [])
    max_questions = session.get("max_questions", settings.DEFAULT_MAX_QUESTIONS)
    current_topic = session.get("current_topic", "Technical Architecture")
    followup_count = session.get("followup_count_for_topic", 0)

    role = get_role_profile(track, role_id)

    # 2. Intermediate Answer Analysis Step
    analysis_data: dict
    if gemini_service.is_configured and payload.last_answer:
        try:
            analysis_prompt = build_intermediate_analysis_prompt(
                track=track,
                role=role,
                difficulty=difficulty,
                question=payload.last_question or "Previous Question",
                answer=payload.last_answer,
                current_topic=current_topic,
                followup_count=followup_count,
            )
            analysis_data = gemini_service.generate_json(
                analysis_prompt,
                INTERMEDIATE_EVALUATION_SCHEMA,
                system_instruction="You are an expert technical interviewer evaluating answer quality and depth.",
                temperature=0.2,
            )
        except GeminiServiceError as exc:
            logger.warning("Intermediate analysis failed, using heuristic: %s", exc)
            analysis_data = _heuristic_intermediate_analysis(
                payload.last_question or "", payload.last_answer or "", followup_count
            )
    else:
        analysis_data = _heuristic_intermediate_analysis(
            payload.last_question or "", payload.last_answer or "", followup_count
        )

    try:
        analysis = IntermediateAnswerAnalysis(**analysis_data)
    except Exception as exc:
        logger.error("Analysis validation failed (%s), defaulting.", exc)
        analysis = IntermediateAnswerAnalysis(
            relevance_score=7.0,
            depth_score=6.5,
            specificity_score=6.0,
            identified_gaps=[],
            detected_claims=[],
            decision="ADVANCE_TOPIC",
            reasoning="Default progression.",
        )

    session_store.record_intermediate_analysis(payload.session_id, analysis.model_dump())

    # 3. Server-Side Deterministic Anti-Loop Logic (Python-enforced)
    # Rules:
    # - If decision == "DRILL_DOWN" AND followup_count < 2 AND turn < max_questions:
    #     Increment followup_count, prompt cross-examination probing gaps or claims.
    # - Else (or if followup_count >= 2):
    #     Append current_topic to topics_covered, pop next topic from topics_remaining, reset followup_count = 0.
    is_followup = False
    turn = payload.question_number
    is_final = turn >= max_questions

    source = "gemini"
    question_data: dict

    if (
        analysis.decision == "DRILL_DOWN"
        and followup_count < 2
        and turn < max_questions
    ):
        # Drill down cross-examination branch
        is_followup = True
        new_followup_count = session_store.step_followup(payload.session_id)
        if gemini_service.is_configured:
            try:
                drill_prompt = build_drilldown_question_prompt(
                    track=track,
                    role=role,
                    difficulty=difficulty,
                    question_number=turn,
                    total_questions=max_questions,
                    current_topic=current_topic,
                    followup_count=new_followup_count,
                    last_question=payload.last_question or "Previous Question",
                    last_answer=payload.last_answer or "Previous Answer",
                    identified_gaps=analysis.identified_gaps,
                    detected_claims=analysis.detected_claims,
                    candidate_profile=candidate_profile,
                )
                question_data = gemini_service.generate_json(
                    drill_prompt,
                    QUESTION_RESPONSE_SCHEMA,
                    system_instruction=INTERVIEWER_SYSTEM_INSTRUCTION,
                )
            except GeminiServiceError as exc:
                logger.warning("Gemini drilldown failed, using fallback: %s", exc)
                question_data = get_fallback_question(track, role_id, turn)
                source = "fallback"
        else:
            question_data = get_fallback_question(track, role_id, turn)
            source = "fallback"
    else:
        # Advance topic branch
        new_topic = session_store.step_advance_topic(payload.session_id)
        current_topic = new_topic
        if gemini_service.is_configured:
            try:
                advance_prompt = build_advance_question_prompt(
                    track=track,
                    role=role,
                    difficulty=difficulty,
                    question_number=turn,
                    total_questions=max_questions,
                    new_topic=new_topic,
                    topics_covered=session.get("topics_covered", []),
                    qa_history=qa_history,
                    resume_summary=resume_summary,
                    job_description=job_description,
                    candidate_profile=candidate_profile,
                )
                question_data = gemini_service.generate_json(
                    advance_prompt,
                    QUESTION_RESPONSE_SCHEMA,
                    system_instruction=INTERVIEWER_SYSTEM_INSTRUCTION,
                )
            except GeminiServiceError as exc:
                logger.warning("Gemini advance question failed, using fallback: %s", exc)
                question_data = get_fallback_question(track, role_id, turn)
                source = "fallback"
        else:
            question_data = get_fallback_question(track, role_id, turn)
            source = "fallback"

    try:
        question = QuestionOut(**question_data)
    except Exception as exc:
        logger.error("Next question validation failed (%s), using fallback.", exc)
        question = QuestionOut(**get_fallback_question(track, role_id, turn))
        source = "fallback"

    session_store.add_question(payload.session_id, question.model_dump())
    updated_session = session_store.get_session(payload.session_id) or session

    return NextQuestionResponse(
        session_id=payload.session_id,
        question_number=turn,
        total_questions=max_questions,
        question=question,
        source=source,
        analysis=analysis,
        current_topic=updated_session.get("current_topic"),
        followup_count=updated_session.get("followup_count_for_topic", 0),
        is_followup=is_followup,
        topics_covered=updated_session.get("topics_covered", []),
        topics_remaining=updated_session.get("topics_remaining", []),
        is_final_question=is_final,
    )


@router.post("/answer")
def submit_answer(payload: AnswerSubmitRequest) -> dict:
    """Records a candidate's answer and speech metrics into the active session."""
    session = session_store.get_session(payload.session_id)
    if session is None:
        logger.warning("Session %s not found in memory", payload.session_id)
        return {"status": "recorded_stateless", "session_id": payload.session_id}

    delivery_dict = payload.delivery_metrics.model_dump() if payload.delivery_metrics else None
    session_store.add_answer(payload.session_id, payload.question, payload.answer, delivery_metrics=delivery_dict)
    return {"status": "ok", "answers_count": len(session["answers_received"])}


@router.post("/evaluate", response_model=InterviewEvaluationResponse)
def evaluate_candidate(payload: InterviewEvaluationRequest) -> InterviewEvaluationResponse:
    """Evaluates the full interview answers with STAR breakdowns and recruiter model rewrites."""
    qa_list = [qa.model_dump() for qa in payload.answers]
    session = session_store.get_session(payload.session_id) if payload.session_id else None
    jd = payload.job_description or (session.get("job_description") if session else None)

    explicit_speech_metrics = (
        [m.model_dump() for m in payload.speech_metrics]
        if payload.speech_metrics
        else (session.get("speech_metrics", []) if session else None)
    )

    result = evaluate_interview(
        track=payload.track,
        role_name=payload.role_name,
        difficulty=payload.difficulty,
        qa_list=qa_list,
        job_description=jd,
        speech_metrics=explicit_speech_metrics,
    )

    if payload.session_id:
        session_store.set_evaluation(payload.session_id, result)

    return InterviewEvaluationResponse(**result)


@router.get("/results/{session_id}")
def get_session_results(session_id: str) -> dict:
    """Fetch stored results and analytics for an interview session."""
    session = session_store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    return session
