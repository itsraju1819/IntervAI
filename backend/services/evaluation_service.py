"""
Evaluation service for IntervAI.

Evaluates candidate interview answers using Gemini AI or deterministic rule-based heuristics.
Includes STAR method structural validation, weakest answer rewrite engine,
speech analytics aggregation, and Job Description keyword alignment.
"""

import logging
import re
from typing import Any

try:
    from roles_config import get_role_profile
    from services.gemini_service import GeminiServiceError, gemini_service
    from services.jd_service import analyze_jd_and_resume
except ImportError:
    from backend.roles_config import get_role_profile
    from backend.services.gemini_service import GeminiServiceError, gemini_service
    from backend.services.jd_service import analyze_jd_and_resume

logger = logging.getLogger("intervai.evaluation")

EVALUATION_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_score": {"type": "integer"},
        "rating": {"type": "string"},
        "summary": {"type": "string"},
        "category_scores": {
            "type": "object",
            "properties": {
                "technical_accuracy": {"type": "integer"},
                "clarity_communication": {"type": "integer"},
                "problem_solving": {"type": "integer"},
                "structure": {"type": "integer"},
            },
            "required": ["technical_accuracy", "clarity_communication", "problem_solving", "structure"],
        },
        "strengths": {
            "type": "array",
            "items": {"type": "string"},
        },
        "improvements": {
            "type": "array",
            "items": {"type": "string"},
        },
        "question_evaluations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "score": {"type": "integer"},
                    "feedback": {"type": "string"},
                },
                "required": ["question", "score", "feedback"],
            },
        },
        "star_breakdown": {
            "type": "object",
            "properties": {
                "situation": {"type": "boolean"},
                "task": {"type": "boolean"},
                "action": {"type": "boolean"},
                "result": {"type": "boolean"},
                "feedback": {"type": "string"},
            },
            "required": ["situation", "task", "action", "result", "feedback"],
        },
        "weakest_answer_rewrite": {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "original_answer": {"type": "string"},
                "critique": {"type": "string"},
                "rewritten_answer": {"type": "string"},
            },
            "required": ["question", "original_answer", "critique", "rewritten_answer"],
        },
        "jd_match_score": {"type": "integer"},
        "matched_keywords": {
            "type": "array",
            "items": {"type": "string"},
        },
        "missing_keywords": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "overall_score",
        "rating",
        "summary",
        "category_scores",
        "strengths",
        "improvements",
        "question_evaluations",
    ],
}


def build_evaluation_prompt(
    track: str,
    role_name: str,
    difficulty: str,
    qa_list: list[dict[str, Any]],
    job_description: str | None = None,
) -> str:
    transcript_blocks = []
    for i, qa in enumerate(qa_list, start=1):
        q = qa.get("question", f"Question {i}")
        a = (qa.get("answer") or "").strip() or "[No answer provided]"
        metrics = qa.get("delivery_metrics")
        metrics_info = ""
        if metrics:
            metrics_info = f" (Pacing: {metrics.get('wpm', 0):.0f} WPM, Fillers: {metrics.get('filler_count', 0)})"
        transcript_blocks.append(f"Question {i}: {q}\nAnswer{metrics_info}: {a}")

    transcript = "\n\n".join(transcript_blocks)

    jd_info = (
        f"\nTarget Job Description Requirements:\n{job_description}\n"
        if job_description
        else "\nNo target Job Description provided.\n"
    )

    return f"""\
You are an elite interview evaluator and recruiter evaluating a candidate's mock interview.

Target Role: {role_name}
Track: {track}
Difficulty: {difficulty}
{jd_info}
Candidate Interview Transcript:
{transcript}

Task:
Perform a comprehensive hiring evaluation:
1. "overall_score": Integer 0 to 100 based on realistic technical and communication standards.
2. "rating": One of "Needs Preparation", "Developing", "Competent", "Very Good", or "Interview Ready".
3. "summary": Executive hiring summary assessing readiness, technical grounding, and communication.
4. "category_scores" (0-100 each):
   - technical_accuracy: accuracy, depth, and proper terminology.
   - clarity_communication: structure, articulateness, and conciseness.
   - problem_solving: logical flow, edge case awareness, trade-offs.
   - structure: use of STAR method, organized framing.
5. "strengths": 2-3 specific demonstrated strengths.
6. "improvements": 2-3 actionable growth areas.
7. "question_evaluations": Individual score (0-100) and actionable 1-2 sentence feedback for each question.
8. "star_breakdown":
   - Explicit boolean validation: situation (bool), task (bool), action (bool), result (bool).
   - feedback (str): Specific notes on how well the candidate structured responses using STAR.
9. "weakest_answer_rewrite":
   - Identify the candidate's single weakest response in the session.
   - "question": The question text.
   - "original_answer": Their raw response.
   - "critique": What made it weak (e.g. lack of metrics, missing actions, vagueness).
   - "rewritten_answer": An optimized, recruiter-ready alternative adhering strictly to the STAR format, preserving the candidate's actual project context.
10. If Job Description is provided, calculate jd_match_score (0-100), matched_keywords, and missing_keywords.
"""


def _aggregate_speech_metrics(
    qa_list: list[dict[str, Any]],
    explicit_metrics: list[dict[str, Any]] | None = None,
) -> tuple[float | None, int | None, str | None]:
    """Computes average WPM and total filler words across turns."""
    collected = []
    if explicit_metrics:
        collected.extend(explicit_metrics)
    for qa in qa_list:
        if qa.get("delivery_metrics"):
            collected.append(qa["delivery_metrics"])

    if not collected:
        return None, None, None

    valid_wpms = [m.get("wpm", 0.0) for m in collected if m.get("wpm", 0.0) > 0]
    total_fillers = sum(int(m.get("filler_count", 0)) for m in collected)
    avg_wpm = round(sum(valid_wpms) / len(valid_wpms), 1) if valid_wpms else 0.0

    if avg_wpm < 110:
        pacing_desc = "Deliberate / slightly slow pacing; aim to respond with greater momentum."
    elif avg_wpm > 175:
        pacing_desc = "Fast speaking pace; remember to pause and articulate key technical nouns."
    else:
        pacing_desc = "Optimal speaking cadence (120-160 WPM), professional and easy to follow."

    if total_fillers > 8:
        filler_desc = f"Noticed {total_fillers} filler words. Practice brief pauses instead of filler words."
    else:
        filler_desc = f"Clean verbal delivery with minimal filler words ({total_fillers} detected)."

    summary = f"{pacing_desc} {filler_desc}"
    return avg_wpm, total_fillers, summary


def evaluate_star_heuristics(all_text: str) -> dict[str, Any]:
    """Deterministic check of STAR method components."""
    lower = all_text.lower()
    has_situation = any(k in lower for k in ["situation", "when i was", "at my", "project where", "company", "team of"])
    has_task = any(k in lower for k in ["task", "responsible for", "goal was", "objective", "needed to", "requirement"])
    has_action = any(k in lower for k in ["i built", "i implemented", "i designed", "i created", "i used", "i decided", "action", "we decided"])
    has_result = any(k in lower for k in ["result", "achieved", "improved", "reduced", "led to", "successfully", "impact", "delivered", "%"])

    missing = []
    if not has_situation:
        missing.append("Situation (context & business backdrop)")
    if not has_task:
        missing.append("Task (your specific role and goal)")
    if not has_action:
        missing.append("Action (the technical steps you personally took)")
    if not has_result:
        missing.append("Result (measurable outcomes & project impact)")

    if missing:
        feedback = f"Work on articulating: {', '.join(missing)}. Quantify results where possible."
    else:
        feedback = "Solid use of the STAR method across your responses with clear context and actions."

    return {
        "situation": has_situation,
        "task": has_task,
        "action": has_action,
        "result": has_result,
        "feedback": feedback,
    }


def build_heuristic_rewrite(weakest_qa: dict[str, Any], role_name: str) -> dict[str, Any]:
    """Constructs a structured STAR rewrite template for the weakest answer."""
    question = weakest_qa.get("question", "Interview Question")
    original = weakest_qa.get("answer", "").strip() or "[No answer provided]"

    critique = (
        "The response was overly brief and lacked concrete STAR structure, "
        "missing specific metrics, architectural decisions, and tangible outcomes."
    )

    rewritten = (
        f"[Situation] In my recent {role_name} project, our system needed to handle increased request volume without latency spikes.\n"
        f"[Task] My objective was to redesign the core pipeline and implement reliable caching and validation.\n"
        f"[Action] I restructured the API endpoints using asynchronous handlers, indexed the primary query keys in PostgreSQL, and added Redis caching for frequent reads.\n"
        f"[Result] This reduced response latency by 35% and maintained 99.9% uptime during peak load testing."
    )

    return {
        "question": question,
        "original_answer": original,
        "critique": critique,
        "rewritten_answer": rewritten,
    }


def heuristic_evaluate(
    track: str,
    role_name: str,
    difficulty: str,
    qa_list: list[dict[str, Any]],
    job_description: str | None = None,
    explicit_metrics: list[dict[str, Any]] | None = None,
    is_unreachable: bool = False,
) -> dict[str, Any]:
    """
    Deterministic rule-based evaluation used when Gemini is offline, unconfigured, or unreachable.
    Calculates objective scores based on answer depth, keywords, and STAR indicators.
    """
    evaluations = []
    scores = []

    role_keywords = {
        "technical": [
            "code", "data", "api", "database", "system", "performance", "testing",
            "frontend", "backend", "python", "java", "sql", "model", "pipeline",
            "debug", "architecture", "scale", "component", "function", "server",
            "async", "query", "index", "cache", "docker", "cloud",
        ],
        "hr_behavioral": [
            "team", "communication", "collaborate", "conflict", "deadline", "lead",
            "learned", "situation", "task", "action", "result", "priority", "feedback",
            "ownership", "empathy", "resolution", "impact",
        ],
    }
    keywords = role_keywords.get(track, role_keywords["technical"])

    all_answers_text = ""
    weakest_idx = 0
    lowest_score = 999

    for idx, qa in enumerate(qa_list):
        q = qa.get("question", "")
        a = (qa.get("answer") or "").strip()
        all_answers_text += " " + a
        words = a.split()
        word_count = len(words)
        lower_a = a.lower()

        # Score based on length, detail, and keyword presence
        if word_count == 0:
            score = 25
            feedback = "No answer was provided for this question. Practice answering aloud with real examples."
        elif word_count < 15:
            score = 55
            feedback = "Answer was too brief. Elaborate with specific details, context, and methodologies."
        elif word_count < 40:
            match_count = sum(1 for kw in keywords if kw in lower_a)
            score = min(80, 65 + match_count * 3)
            feedback = "Good foundation. Expand on your specific architectural trade-offs, metrics, and outcomes."
        elif word_count < 100:
            match_count = sum(1 for kw in keywords if kw in lower_a)
            score = min(92, 75 + match_count * 2)
            feedback = "Strong and well-articulated response with relevant technical details and logical flow."
        else:
            match_count = sum(1 for kw in keywords if kw in lower_a)
            score = min(95, 80 + match_count * 2)
            feedback = "Comprehensive and thorough response demonstrating clear subject familiarity and ownership."

        if score < lowest_score:
            lowest_score = score
            weakest_idx = idx

        evaluations.append({
            "question": q,
            "score": score,
            "feedback": feedback,
            "delivery_metrics": qa.get("delivery_metrics"),
        })
        scores.append(score)

    avg_score = int(sum(scores) / max(len(scores), 1))

    if avg_score >= 85:
        rating = "Interview Ready"
    elif avg_score >= 75:
        rating = "Very Good"
    elif avg_score >= 65:
        rating = "Competent"
    elif avg_score >= 50:
        rating = "Developing"
    else:
        rating = "Needs Preparation"

    summary = (
        f"You completed your {role_name} interview ({difficulty} level) under deterministic heuristic evaluation. "
        "Your responses demonstrated foundational competency, and expanding on specific measurable "
        "metrics and STAR trade-offs will help you stand out to hiring managers."
    )

    strengths = [
        f"Demonstrated clear understanding of core {role_name} competencies",
        "Directly addressed the interview questions with relevant contextual examples",
        "Professional tone and structured thought progression across responses",
    ]

    improvements = [
        "Incorporate the STAR framework (Situation, Task, Action, Result) for all scenario questions",
        "Mention specific tools, libraries, or architectural trade-offs when explaining technical choices",
        "Quantify your accomplishments (e.g. % performance improvement, latency, users served) where applicable",
    ]

    # Star evaluation and rewrite
    star_breakdown = evaluate_star_heuristics(all_answers_text)
    weakest_qa = qa_list[weakest_idx] if qa_list else {"question": "Q1", "answer": ""}
    weakest_rewrite = build_heuristic_rewrite(weakest_qa, role_name)

    # Speech metrics aggregation
    avg_wpm, total_fillers, speech_summary = _aggregate_speech_metrics(qa_list, explicit_metrics)

    # JD alignment analysis
    jd_analysis = analyze_jd_and_resume(job_description or "", all_answers_text)
    jd_match_score = jd_analysis["match_score"] if job_description else None
    matched_keywords = jd_analysis["matched_skills"] if job_description else None
    missing_keywords = jd_analysis["missing_skills"] if job_description else None

    status_str = "evaluator_unreachable" if is_unreachable else "heuristic_evaluated"
    msg_str = (
        "AI evaluation service could not be reached. Local heuristic evaluation applied."
        if is_unreachable
        else "Deterministic heuristic evaluation applied (AI service unconfigured or offline)."
    )

    return {
        "overall_score": avg_score,
        "rating": rating,
        "summary": summary,
        "category_scores": {
            "technical_accuracy": min(100, max(40, avg_score + 1)),
            "clarity_communication": min(100, max(45, avg_score + 2)),
            "problem_solving": min(100, max(40, avg_score - 2)),
            "structure": min(100, max(40, avg_score - 1)),
        },
        "strengths": strengths,
        "improvements": improvements,
        "question_evaluations": evaluations,
        "star_breakdown": star_breakdown,
        "weakest_answer_rewrite": weakest_rewrite,
        "average_wpm": avg_wpm,
        "total_filler_words": total_fillers,
        "speech_delivery_summary": speech_summary,
        "jd_match_score": jd_match_score,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "source": "heuristic_fallback",
        "is_fallback": True,
        "evaluation_status": status_str,
        "message": msg_str,
    }


def evaluate_interview(
    track: str,
    role_name: str,
    difficulty: str,
    qa_list: list[dict[str, Any]],
    job_description: str | None = None,
    speech_metrics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluates interview answers with Gemini or deterministic heuristic fallback."""
    avg_wpm, total_fillers, speech_summary = _aggregate_speech_metrics(qa_list, speech_metrics)

    if gemini_service.is_configured:
        try:
            prompt = build_evaluation_prompt(track, role_name, difficulty, qa_list, job_description)
            result = gemini_service.generate_json(
                prompt,
                EVALUATION_SCHEMA,
                system_instruction="You are an expert technical interviewer and student hiring mentor.",
                temperature=0.3,
            )
            result["source"] = "gemini"
            result["is_fallback"] = False
            result["evaluation_status"] = "completed"
            result["average_wpm"] = avg_wpm
            result["total_filler_words"] = total_fillers
            result["speech_delivery_summary"] = speech_summary

            # Ensure star_breakdown exists
            if not result.get("star_breakdown"):
                all_text = " ".join((q.get("answer") or "") for q in qa_list)
                result["star_breakdown"] = evaluate_star_heuristics(all_text)

            # Ensure weakest_answer_rewrite exists
            if not result.get("weakest_answer_rewrite") and qa_list:
                result["weakest_answer_rewrite"] = build_heuristic_rewrite(qa_list[0], role_name)

            # If Gemini did not populate JD fields, fill from jd_service
            if job_description and ("jd_match_score" not in result or result["jd_match_score"] is None):
                all_ans = " ".join((q.get("answer") or "") for q in qa_list)
                jd_res = analyze_jd_and_resume(job_description, all_ans)
                result["jd_match_score"] = jd_res["match_score"]
                result["matched_keywords"] = jd_res["matched_skills"]
                result["missing_keywords"] = jd_res["missing_skills"]

            return result
        except GeminiServiceError as exc:
            logger.warning("Gemini evaluation call failed, falling back to heuristic: %s", exc)

    return heuristic_evaluate(
        track,
        role_name,
        difficulty,
        qa_list,
        job_description,
        explicit_metrics=speech_metrics,
        is_unreachable=False,
    )
