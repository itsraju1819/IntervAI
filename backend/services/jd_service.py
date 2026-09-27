"""
Job Description (JD) processing and skill alignment service for IntervAI.

Extracts key competencies, required tech stack, and calculates
Resume vs Job Description match score to empower students.
"""

import logging
import re
from typing import Any
try:
    from services.resume_service import COMMON_SKILLS
except ImportError:
    from backend.services.resume_service import COMMON_SKILLS

logger = logging.getLogger("intervai.jd")


def extract_jd_skills(jd_text: str) -> list[str]:
    """Finds known technical and behavioral skills in a Job Description."""
    if not jd_text:
        return []
    lower_jd = jd_text.lower()
    matched = [s for s in COMMON_SKILLS if re.search(r"\b" + re.escape(s) + r"\b", lower_jd)]
    return sorted(list(set(matched)))


def analyze_jd_and_resume(jd_text: str, resume_text: str | None = None, resume_skills: list[str] | None = None) -> dict[str, Any]:
    """
    Analyzes JD requirements, extracts core competencies, and compares
    against candidate's resume to provide a match score and actionable feedback.
    """
    if not jd_text or not jd_text.strip():
        return {
            "has_jd": False,
            "jd_skills": [],
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "summary": "No job description provided.",
        }

    jd_skills = extract_jd_skills(jd_text)

    # Candidate skills from parsed list or text scan
    cand_skills = set(s.lower() for s in (resume_skills or []))
    if resume_text and not cand_skills:
        lower_resume = resume_text.lower()
        cand_skills = set(s for s in COMMON_SKILLS if re.search(r"\b" + re.escape(s) + r"\b", lower_resume))

    jd_set = set(jd_skills)
    matched = sorted(list(jd_set.intersection(cand_skills)))
    missing = sorted(list(jd_set.difference(cand_skills)))

    # Calculate match percentage
    if jd_set:
        match_score = int((len(matched) / len(jd_set)) * 100)
    else:
        # Fallback if no predefined skills explicitly detected
        match_score = 75 if resume_text else 50

    # Clean concise summary of JD (first 500 characters)
    clean_lines = [line.strip() for line in jd_text.splitlines() if line.strip()]
    condensed_jd = " ".join(clean_lines[:15])[:600]

    return {
        "has_jd": True,
        "jd_skills": jd_skills,
        "match_score": min(100, max(20, match_score)),
        "matched_skills": matched,
        "missing_skills": missing,
        "summary": condensed_jd,
    }
