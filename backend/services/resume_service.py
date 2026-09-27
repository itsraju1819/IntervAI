"""
Resume parsing and extraction service for IntervAI.

Performs deep resume structuring using pdfplumber and Gemini structured output,
extracting verified project claims, technical stack, metrics, and seniority.
"""

import io
import logging
import re
from typing import Any

import pdfplumber
import pypdf

try:
    from services.gemini_service import GeminiServiceError, gemini_service
except ImportError:
    from backend.services.gemini_service import GeminiServiceError, gemini_service

logger = logging.getLogger("intervai.resume")

COMMON_SKILLS = [
    # Programming Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "ruby", "php", "sql", "html", "css",
    # Frameworks & Libraries
    "react", "angular", "vue", "next.js", "node.js", "express", "fastapi", "django", "flask",
    "spring", "spring boot", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
    # Databases & Cloud Tools
    "postgresql", "mysql", "mongodb", "redis", "sqlite", "elasticsearch", "git", "github",
    "docker", "kubernetes", "aws", "azure", "gcp", "linux", "rest api", "graphql", "ci/cd"
]

CANDIDATE_PROFILE_SCHEMA = {
    "type": "object",
    "properties": {
        "technical_stack": {
            "type": "array",
            "items": {"type": "string"},
        },
        "key_projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string"},
                    "claimed_metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "core_technologies": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["project_name", "claimed_metrics", "core_technologies"],
            },
        },
        "experience_level": {
            "type": "string",
            "description": "Junior | Mid-Level | Senior | Student/Intern",
        },
        "summary": {
            "type": "string",
            "description": "Concise summary of experience and engineering achievements",
        },
    },
    "required": ["technical_stack", "key_projects", "experience_level", "summary"],
}


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extracts raw text from PDF file bytes using pdfplumber with pypdf fallback."""
    # Primary parser: pdfplumber for robust layout and tabular text handling
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages_text = []
            for page in pdf.pages:
                extracted = page.extract_text() or ""
                if extracted.strip():
                    pages_text.append(extracted.strip())
            if pages_text:
                return "\n\n".join(pages_text)
    except Exception as exc:
        logger.warning("pdfplumber extraction failed, attempting pypdf fallback: %s", exc)

    # Secondary fallback: pypdf
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        extracted_text = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                extracted_text.append(text.strip())
        return "\n\n".join(extracted_text)
    except Exception as exc:
        logger.error("All PDF parsers failed on document bytes: %s", exc)
        return ""


def heuristic_extract_profile(raw_text: str, matched_skills: list[str]) -> dict[str, Any]:
    """Fallback heuristic profile builder when AI extraction is unavailable."""
    lower_text = raw_text.lower()

    # Determine seniority
    if any(k in lower_text for k in ["senior", "lead", "architect", "staff engineer"]):
        experience_level = "Senior"
    elif any(k in lower_text for k in ["mid-level", "experienced", "software engineer ii"]):
        experience_level = "Mid-Level"
    elif any(k in lower_text for k in ["intern", "student", "fresher", "junior", "entry level", "graduate"]):
        experience_level = "Junior / Intern"
    else:
        experience_level = "Mid-Level"

    # Heuristic project detection
    projects = []
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    project_headers = []
    for line in lines:
        if any(w in line.lower() for w in ["project:", "built", "developed", "created", "designed"]) and len(line) < 100:
            project_headers.append(line)

    metric_regex = re.compile(r"(\b\d+[\d,.]*\s*(?:%|x|ms|s|users|requests|qps|stars|records|mb|gb|tb)\b|\b(?:reduced|improved|increased|optimized|scaled|accelerated)\b[^\n,.]*)", re.IGNORECASE)

    if project_headers:
        for idx, header in enumerate(project_headers[:3]):
            claims = metric_regex.findall(raw_text)
            projects.append({
                "project_name": header[:60],
                "claimed_metrics": claims[:2] if claims else ["Engineered end-to-end functionality"],
                "core_technologies": [s for s in matched_skills[:4]],
            })
    else:
        # Default placeholder project based on detected skills
        projects.append({
            "project_name": "Core Technical Application",
            "claimed_metrics": ["Production deployment and system optimization"],
            "core_technologies": matched_skills[:4],
        })

    cleaned_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    condensed_text = " ".join(cleaned_lines[:40])[:1200]

    return {
        "technical_stack": matched_skills,
        "key_projects": projects,
        "experience_level": experience_level,
        "summary": condensed_text,
    }


def parse_resume(pdf_bytes: bytes, filename: str = "resume.pdf") -> dict[str, Any]:
    """
    Parses resume PDF bytes using pdfplumber + Gemini structured output.
    Extracts structured technical stack, projects, claimed metrics, and seniority.
    """
    text = extract_text_from_pdf(pdf_bytes)
    if not text:
        return {
            "filename": filename,
            "success": False,
            "text": "",
            "skills": [],
            "summary": "Could not extract text from the provided document.",
            "candidate_profile": None,
        }

    lower_text = text.lower()
    matched_skills = [s for s in COMMON_SKILLS if re.search(r"\b" + re.escape(s) + r"\b", lower_text)]

    candidate_profile = None

    if gemini_service.is_configured:
        try:
            prompt = f"""\
You are an expert technical recruiter analyzing an engineering resume.
Extract a structured candidate profile from the resume text below:

RESUME TEXT:
{text[:4000]}

Extract:
1. "technical_stack": Comprehensive list of programming languages, libraries, frameworks, databases, and DevOps tools explicitly mentioned.
2. "key_projects": Array of objects for major projects. For each project include:
   - "project_name": Title or name of the project.
   - "claimed_metrics": Specific quantitative achievements (e.g. "Reduced API latency by 35%", "Served 10k daily active users", "Processed 1M records"). If no metric was stated, extract the primary functional milestone.
   - "core_technologies": Technologies used specifically for this project.
3. "experience_level": One of "Junior / Intern", "Mid-Level", "Senior", or "Lead".
4. "summary": A concise 2-3 sentence recruiter brief highlighting the candidate's core domain and standout projects.
"""
            candidate_profile = gemini_service.generate_json(
                prompt,
                CANDIDATE_PROFILE_SCHEMA,
                system_instruction="You are an expert technical hiring manager and resume parser.",
                temperature=0.2,
            )
        except GeminiServiceError as exc:
            logger.warning("Gemini resume structuring failed, falling back to heuristic: %s", exc)

    if not candidate_profile:
        candidate_profile = heuristic_extract_profile(text, matched_skills)

    # Merge skills from AI and regex
    all_skills = sorted(list(set(matched_skills + candidate_profile.get("technical_stack", []))))
    candidate_profile["technical_stack"] = all_skills

    return {
        "filename": filename,
        "success": True,
        "text": text,
        "skills": all_skills,
        "summary": candidate_profile.get("summary", ""),
        "candidate_profile": candidate_profile,
    }
