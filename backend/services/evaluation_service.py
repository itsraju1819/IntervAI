"""
Evaluation service for IntervAI.

Evaluates candidate interview answers using Gemini AI, with an intelligent
rule-based heuristic fallback if Gemini is offline or not configured.
Includes Job Description alignment metrics and student growth points.
"""

import logging
from typing import Any

from roles_config import get_role_profile
from services.gemini_service import GeminiServiceError, gemini_service
from services.jd_service import analyze_jd_and_resume

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
    qa_list: list[dict[str, str]],
    job_description: str | None = None,
) -> str:
    transcript = "\n\n".join(
        f"Question {i+1}: {qa.get('question')}\nAnswer: {qa.get('answer', '').strip() or '[No answer provided]'}"
        for i, qa in enumerate(qa_list)
    )

    jd_info = (
        f"\nTarget Job Description Requirements:\n{job_description}\n"
        if job_description
        else "\nNo target Job Description provided.\n"
    )

    return f"""\
You are an expert interview evaluator and student hiring mentor evaluating a candidate's mock interview.

Target Role: {role_name}
Track: {track}
Difficulty: {difficulty}
{jd_info}
Candidate Interview Transcript:
{transcript}

Task:
Evaluate the candidate's answers comprehensively:
1. Overall score from 0 to 100.
2. Select a rating: "Needs Preparation", "Developing", "Competent", "Very Good", or "Interview Ready".
3. Provide an encouraging yet rigorous executive summary.
4. Score 4 categories (0-100):
   - technical_accuracy: correctness, depth, terminology
   - clarity_communication: articulate, structured, easy to follow
   - problem_solving: logical thought process, reasoning, trade-offs
   - structure: use of STAR method, clear examples, organized flow
5. 2-3 specific strengths demonstrated.
6. 2-3 actionable areas for student improvement.
7. For each question, provide an individual score (0-100) and 1-2 sentences of feedback.
8. If Job Description is provided, calculate jd_match_score (0-100), matched_keywords, and missing_keywords.
"""


def heuristic_evaluate(
    track: str,
    role_name: str,
    difficulty: str,
    qa_list: list[dict[str, str]],
    job_description: str | None = None,
) -> dict[str, Any]:
    """Smart heuristic evaluator used when Gemini is offline or unconfigured."""
    evaluations = []
    scores = []

    role_keywords = {
        "technical": [
            "code", "data", "api", "database", "system", "performance", "testing",
            "frontend", "backend", "python", "java", "sql", "model", "pipeline",
            "debug", "architecture", "scale", "component", "function", "server",
        ],
        "hr_behavioral": [
            "team", "communication", "collaborate", "conflict", "deadline", "lead",
            "learned", "situation", "task", "action", "result", "priority", "feedback",
        ],
    }
    keywords = role_keywords.get(track, role_keywords["technical"])

    all_answers_text = ""
    for qa in qa_list:
        q = qa.get("question", "")
        a = (qa.get("answer") or "").strip()
        all_answers_text += " " + a
        words = a.split()
        word_count = len(words)
        lower_a = a.lower()

        # Score based on length, detail, and keyword presence
        if word_count == 0:
            score = 25
            feedback = "No answer was provided for this question. Practice answering aloud."
        elif word_count < 15:
            score = 55
            feedback = "Answer was too brief. Elaborate with specific details and context."
        elif word_count < 40:
            match_count = sum(1 for kw in keywords if kw in lower_a)
            score = min(80, 65 + match_count * 3)
            feedback = "Good foundation. Expand on your specific methodology, trade-offs, and results."
        elif word_count < 100:
            match_count = sum(1 for kw in keywords if kw in lower_a)
            score = min(92, 78 + match_count * 2)
            feedback = "Strong and well-articulated response with relevant details and logical flow."
        else:
            score = 90
            feedback = "Comprehensive and thorough response demonstrating clear subject familiarity."

        evaluations.append({
            "question": q,
            "score": score,
            "feedback": feedback,
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
        f"You demonstrated good preparation for the {role_name} interview ({difficulty} level). "
        "Your answers showed practical understanding, and expanding on specific measurable "
        "outcomes will help you stand out even further."
    )

    strengths = [
        f"Demonstrated clear understanding of core {role_name} responsibilities",
        "Directly addressed the interview questions with relevant context",
        "Professional tone and structured thought progression",
    ]

    improvements = [
        "Incorporate the STAR framework (Situation, Task, Action, Result) for situational questions",
        "Mention specific tools, libraries, or architectural trade-offs when explaining technical choices",
        "Quantify your accomplishments (e.g. % performance improvement, time saved) where applicable",
    ]

    # JD alignment analysis
    jd_analysis = analyze_jd_and_resume(job_description or "", all_answers_text)
    jd_match_score = jd_analysis["match_score"] if job_description else None
    matched_keywords = jd_analysis["matched_skills"] if job_description else None
    missing_keywords = jd_analysis["missing_skills"] if job_description else None

    return {
        "overall_score": avg_score,
        "rating": rating,
        "summary": summary,
        "category_scores": {
            "technical_accuracy": min(100, max(40, avg_score + 2)),
            "clarity_communication": min(100, max(45, avg_score + 3)),
            "problem_solving": min(100, max(40, avg_score - 2)),
            "structure": min(100, max(40, avg_score - 1)),
        },
        "strengths": strengths,
        "improvements": improvements,
        "question_evaluations": evaluations,
        "jd_match_score": jd_match_score,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "source": "heuristic_fallback",
    }


def evaluate_interview(
    track: str,
    role_name: str,
    difficulty: str,
    qa_list: list[dict[str, str]],
    job_description: str | None = None,
) -> dict[str, Any]:
    """Evaluates interview answers with Gemini or the smart heuristic fallback."""
    if gemini_service.is_configured:
        try:
            prompt = build_evaluation_prompt(track, role_name, difficulty, qa_list, job_description)
            result = gemini_service.generate_json(
                prompt,
                EVALUATION_SCHEMA,
                system_instruction="You are an expert technical interviewer and student hiring mentor.",
            )
            result["source"] = "gemini"

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

    return heuristic_evaluate(track, role_name, difficulty, qa_list, job_description)
