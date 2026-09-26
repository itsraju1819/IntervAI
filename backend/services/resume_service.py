"""
Resume parsing and extraction service for IntervAI.

Extracts text, identifies key skills, and prepares resume context
to personalize interview questions.
"""

import io
import logging
import re
from typing import Any
import pypdf

logger = logging.getLogger("intervai.resume")

COMMON_SKILLS = [
    # Programming Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "ruby", "php", "sql", "html", "css",
    # Frameworks & Libraries
    "react", "angular", "vue", "next.js", "node.js", "express", "fastapi", "django", "flask",
    "spring", "spring boot", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
    # Databases & Tools
    "postgresql", "mysql", "mongodb", "redis", "sqlite", "elasticsearch", "git", "github",
    "docker", "kubernetes", "aws", "azure", "gcp", "linux", "rest api", "graphql", "ci/cd"
]


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extracts raw text from PDF file bytes safely."""
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        extracted_text = []
        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                extracted_text.append(text.strip())
        return "\n\n".join(extracted_text)
    except Exception as exc:
        logger.error("Failed to parse PDF bytes: %s", exc)
        return ""


def parse_resume(pdf_bytes: bytes, filename: str = "resume.pdf") -> dict[str, Any]:
    """
    Parses resume PDF bytes, extracts text, finds matching skills,
    and returns a structured profile summary.
    """
    text = extract_text_from_pdf(pdf_bytes)
    if not text:
        return {
            "filename": filename,
            "success": False,
            "text": "",
            "skills": [],
            "summary": "Could not extract text from the provided document.",
        }

    lower_text = text.lower()
    matched_skills = [s for s in COMMON_SKILLS if re.search(r"\b" + re.escape(s) + r"\b", lower_text)]

    # Take first 1500 characters as a concise contextual summary for prompts
    cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]
    condensed_text = " ".join(cleaned_lines[:40])[:1200]

    return {
        "filename": filename,
        "success": True,
        "text": text,
        "skills": matched_skills,
        "summary": condensed_text,
    }
