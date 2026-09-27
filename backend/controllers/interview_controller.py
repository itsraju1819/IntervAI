"""
Interview controller for IntervAI.

Orchestrates request handling, security validations, rate limiting,
FSM state progression, and service invocations between the HTTP layer and core logic.
"""

from typing import Any
from fastapi import Request, UploadFile

try:
    from config import settings
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
        QuestionOut,
        ResumeUploadResponse,
    )
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
    from services import session_store
    from services.evaluation_service import evaluate_interview
    from services.fallback_questions import get_fallback_opening_question, get_fallback_question
    from services.gemini_service import GeminiServiceError, gemini_service
    from services.jd_service import analyze_jd_and_resume
    from services.resume_service import parse_resume
    from utils.errors import AppValidationError, NotFoundError, RateLimitExceededError, SecurityError
    from utils.logger import app_logger
    from utils.security import general_limiter, sanitize_text, upload_limiter, validate_pdf_signature
except ImportError:
    from backend.config import settings
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
        QuestionOut,
        ResumeUploadResponse,
    )
    from backend.prompts.interviewer_prompt import (
        INTERMEDIATE_EVALUATION_SCHEMA,
        INTERVIEWER_SYSTEM_INSTRUCTION,
        QUESTION_RESPONSE_SCHEMA,
        build_advance_question_prompt,
        build_drilldown_question_prompt,
        build_intermediate_analysis_prompt,
        build_opening_question_prompt,
    )
    from backend.roles_config import TRACKS, get_role_profile, list_technical_roles
    from backend.services import session_store
    from backend.services.evaluation_service import evaluate_interview
    from backend.services.fallback_questions import get_fallback_opening_question, get_fallback_question
    from backend.services.gemini_service import GeminiServiceError, gemini_service
    from backend.services.jd_service import analyze_jd_and_resume
    from backend.services.resume_service import parse_resume
    from backend.utils.errors import AppValidationError, NotFoundError, RateLimitExceededError, SecurityError
    from backend.utils.logger import app_logger
    from backend.utils.security import general_limiter, sanitize_text, upload_limiter, validate_pdf_signature


class InterviewController:
    """Controller class handling business orchestration for mock interview workflows."""

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extracts client IP, respecting proxy headers if set."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "127.0.0.1"

    @classmethod
    def get_roles(cls) -> dict[str, Any]:
        """Provides track and role profiles for the frontend setup interface."""
        return {
            "tracks": TRACKS,
            "technical_roles": list_technical_roles(),
        }

    @classmethod
    async def upload_resume(cls, request: Request, file: UploadFile) -> ResumeUploadResponse:
        """Validates PDF file signature, enforces rate limits, and extracts profile."""
        client_ip = cls._get_client_ip(request)
        allowed, retry_after = upload_limiter.is_allowed(client_ip)
        if not allowed:
            raise RateLimitExceededError(retry_after)

        raw_filename = sanitize_text(file.filename or "resume.pdf", max_length=200)
        if not raw_filename.lower().endswith(".pdf"):
            raise SecurityError("Only authentic PDF documents (.pdf) are permitted.")

        content = await file.read()
        if not validate_pdf_signature(content):
            raise SecurityError("Invalid file format. The file is corrupted or not a valid PDF document.")

        try:
            parsed = parse_resume(content, filename=raw_filename)
            app_logger.info("Resume parsed successfully for filename: %s", raw_filename)
            return ResumeUploadResponse(**parsed)
        except Exception as exc:
            app_logger.error("Failed to process resume: %s", exc)
            raise AppValidationError("Could not parse the provided resume document.") from exc

    @classmethod
    def analyze_job_description(cls, request: Request, payload: AnalyzeJdRequest) -> AnalyzeJdResponse:
        """Compares target job requirements against candidate competencies."""
        client_ip = cls._get_client_ip(request)
        allowed, retry_after = general_limiter.is_allowed(client_ip)
        if not allowed:
            raise RateLimitExceededError(retry_after)

        result = analyze_jd_and_resume(
            payload.job_description,
            resume_text=payload.resume_summary,
            resume_skills=payload.resume_skills,
        )
        return AnalyzeJdResponse(**result)

    @classmethod
    def start_interview(cls, request: Request, payload: InterviewStartRequest) -> InterviewStartResponse:
        """Initializes a new session in session_store with FSM tracking and opening question."""
        client_ip = cls._get_client_ip(request)
        allowed, retry_after = general_limiter.is_allowed(client_ip)
        if not allowed:
            raise RateLimitExceededError(retry_after)

        if payload.track not in TRACKS:
            raise AppValidationError(f"Invalid interview track: {payload.track!r}")

        if payload.track == "technical" and not payload.role_id:
            raise AppValidationError("role_id is required for the technical track.")

        try:
            role = get_role_profile(payload.track, payload.role_id)
        except ValueError as exc:
            raise AppValidationError(str(exc)) from exc

        total_questions = payload.max_questions or settings.DEFAULT_MAX_QUESTIONS
        expected_topics = list(role.get("expected_topics", ["Core Fundamentals"]))
        candidate_profile_dict = payload.candidate_profile.model_dump() if payload.candidate_profile else None

        source = "gemini"
        question_data: dict[str, Any]

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
                app_logger.warning("Gemini opening question failed, utilizing fallback bank: %s", exc)
                question_data = get_fallback_opening_question(payload.track, payload.role_id)
                source = "fallback"
        else:
            app_logger.info("Gemini not configured on server; using calibrated fallback bank.")
            question_data = get_fallback_opening_question(payload.track, payload.role_id)
            source = "fallback"

        try:
            question = QuestionOut(**question_data)
        except Exception as exc:
            app_logger.error("Question validation failed (%s), defaulting to fallback.", exc)
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

    @classmethod
    def get_next_question(cls, request: Request, payload: NextQuestionRequest) -> NextQuestionResponse:
        """
        Executes intermediate answer evaluation, enforces server-side anti-loop caps (max 2 follow-ups),
        and dynamically generates either a cross-examination follow-up or advances to the next topic.
        """
        client_ip = cls._get_client_ip(request)
        allowed, retry_after = general_limiter.is_allowed(client_ip)
        if not allowed:
            raise RateLimitExceededError(retry_after)

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

        # Intermediate Answer Analysis Step
        analysis_data: dict[str, Any]
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
                app_logger.warning("Intermediate analysis failed, using heuristic: %s", exc)
                analysis_data = cls._heuristic_analysis(payload.last_answer or "", followup_count)
        else:
            analysis_data = cls._heuristic_analysis(payload.last_answer or "", followup_count)

        from models.schemas import IntermediateAnswerAnalysis
        analysis = IntermediateAnswerAnalysis(**analysis_data)
        session_store.record_intermediate_analysis(payload.session_id, analysis.model_dump())

        # Anti-Loop Transition Engine
        turn = payload.question_number
        is_final = turn >= max_questions
        is_followup = False

        source = "gemini"
        question_data: dict[str, Any]

        if analysis.decision == "DRILL_DOWN" and followup_count < 2 and turn < max_questions:
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
                    app_logger.warning("Gemini drilldown failed, falling back: %s", exc)
                    question_data = get_fallback_question(track, role_id, turn)
                    source = "fallback"
            else:
                question_data = get_fallback_question(track, role_id, turn)
                source = "fallback"
        else:
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
                    app_logger.warning("Gemini advance question failed, falling back: %s", exc)
                    question_data = get_fallback_question(track, role_id, turn)
                    source = "fallback"
            else:
                question_data = get_fallback_question(track, role_id, turn)
                source = "fallback"

        try:
            question = QuestionOut(**question_data)
        except Exception as exc:
            app_logger.error("Next question schema validation failed (%s), using fallback.", exc)
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

    @classmethod
    def submit_answer(cls, request: Request, payload: AnswerSubmitRequest) -> dict[str, Any]:
        """Records candidate response and speech metrics into session state."""
        session = session_store.get_session(payload.session_id)
        if session is None:
            return {"status": "recorded_stateless", "session_id": payload.session_id}

        delivery_dict = payload.delivery_metrics.model_dump() if payload.delivery_metrics else None
        session_store.add_answer(
            payload.session_id,
            payload.question,
            payload.answer,
            delivery_metrics=delivery_dict,
        )
        return {"status": "ok", "answers_count": len(session["answers_received"])}

    @classmethod
    def evaluate_candidate(cls, request: Request, payload: InterviewEvaluationRequest) -> InterviewEvaluationResponse:
        """Evaluates full interview with STAR verification and model answer rewrite engine."""
        client_ip = cls._get_client_ip(request)
        allowed, retry_after = general_limiter.is_allowed(client_ip)
        if not allowed:
            raise RateLimitExceededError(retry_after)

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

    @classmethod
    def get_session_results(cls, session_id: str) -> dict[str, Any]:
        """Retrieves scorecard and analytics for a completed session."""
        session = session_store.get_session(session_id)
        if session is None:
            raise NotFoundError("Interview session not found.")
        return session

    @staticmethod
    def _heuristic_analysis(answer: str, followup_count: int) -> dict[str, Any]:
        """Heuristic answer assessment when AI service is offline."""
        words = answer.split()
        if len(words) < 20:
            return {
                "relevance_score": 5.0,
                "depth_score": 3.5,
                "specificity_score": 3.0,
                "identified_gaps": ["Concise answer requires deeper technical explanation."],
                "detected_claims": [],
                "decision": "DRILL_DOWN" if followup_count < 2 else "ADVANCE_TOPIC",
                "reasoning": "Answer was brief; cross-examination recommended.",
            }
        return {
            "relevance_score": 8.0,
            "depth_score": 7.5,
            "specificity_score": 7.0,
            "identified_gaps": ["Can expand on edge cases."],
            "detected_claims": ["Stated architectural experience."],
            "decision": "DRILL_DOWN" if followup_count < 1 else "ADVANCE_TOPIC",
            "reasoning": "Solid baseline; advancing topic or probing trade-off.",
        }
