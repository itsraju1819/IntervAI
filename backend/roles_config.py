"""
Role and track configuration for IntervAI.

This is intentionally plain Python data (not a database table) — for a
college project it needs to be easy to read, easy to extend, and easy to
explain in a viva: "adding a new role means adding one dictionary entry,
nothing else in the app changes."

Two tracks are supported (see <interview_tracks> in the project spec):
  - "hr_behavioral": no specific technical role, evaluates soft skills.
  - "technical": role-specific, pulled from TECHNICAL_ROLES below.

To add a new technical role: add one entry to TECHNICAL_ROLES. Every
service that generates prompts (question generation, answer analysis,
final evaluation) reads from this file rather than hardcoding role facts.
"""

from typing import TypedDict


class RoleProfile(TypedDict):
    role_id: str
    role_name: str
    description: str
    core_skills: list[str]
    secondary_skills: list[str]
    expected_topics: list[str]
    question_types: list[str]
    difficulty_guidelines: dict[str, str]
    project_question_strategy: str
    behavioral_overlap: list[str]
    evaluation_focus: list[str]


TECHNICAL_ROLES: dict[str, RoleProfile] = {
    "full_stack_developer": {
        "role_id": "full_stack_developer",
        "role_name": "Full-Stack Developer",
        "description": (
            "Builds both the client-facing and server-side parts of web "
            "applications, including the data layer that connects them."
        ),
        "core_skills": [
            "frontend fundamentals (HTML/CSS/JS or a framework)",
            "backend/API design",
            "databases",
            "authentication",
            "deployment",
            "system design basics",
        ],
        "secondary_skills": ["testing", "caching", "version control", "CI/CD"],
        "expected_topics": [
            "frontend", "backend", "APIs", "databases", "authentication", "deployment",
        ],
        "question_types": ["conceptual", "project-based", "debugging", "architecture", "trade-off"],
        "difficulty_guidelines": {
            "beginner": "fundamentals, definitions, basic examples (e.g. what is a REST API)",
            "intermediate": "implementation and reasoning (e.g. how would you structure an API for X)",
            "advanced": "architecture, trade-offs, scaling, edge cases (e.g. how would you handle X at scale)",
        },
        "project_question_strategy": (
            "Prefer questions grounded in the candidate's resume projects; "
            "ask about architecture decisions, integration between frontend "
            "and backend, and deployment choices they actually made."
        ),
        "behavioral_overlap": ["teamwork", "handling deadlines", "code review feedback"],
        "evaluation_focus": ["technical_accuracy", "depth", "specificity", "relevance", "clarity"],
    },
    "ml_engineer": {
        "role_id": "ml_engineer",
        "role_name": "ML Engineer",
        "description": (
            "Builds, evaluates, and deploys machine learning models, "
            "including the data pipeline around them."
        ),
        "core_skills": [
            "Python", "machine learning", "statistics", "data preprocessing",
            "feature engineering", "model evaluation", "deployment",
        ],
        "secondary_skills": ["MLOps", "experiment tracking", "data visualization"],
        "expected_topics": [
            "data preprocessing", "model selection", "evaluation metrics",
            "overfitting/generalization", "deployment", "project experience",
        ],
        "question_types": ["conceptual", "scenario", "project-based", "debugging", "architecture", "trade-off"],
        "difficulty_guidelines": {
            "beginner": "fundamentals, definitions, basic examples (e.g. what is overfitting)",
            "intermediate": "applying a technique and reasoning about a choice (e.g. why this metric)",
            "advanced": "trade-offs, architecture, edge cases (e.g. handling severe class imbalance at scale)",
        },
        "project_question_strategy": (
            "Ground questions in the candidate's stated ML projects; ask "
            "about data preparation, model choice reasoning, evaluation "
            "methodology, and any metrics they claim — without assuming "
            "specific algorithms unless the resume names them."
        ),
        "behavioral_overlap": ["handling ambiguous problems", "communicating results to non-technical people"],
        "evaluation_focus": ["technical_accuracy", "depth", "specificity", "relevance", "clarity"],
    },
    "data_analyst": {
        "role_id": "data_analyst",
        "role_name": "Data Analyst",
        "description": (
            "Extracts, cleans, and interprets data to answer business "
            "questions and support decisions."
        ),
        "core_skills": ["SQL", "Python", "statistics", "data cleaning", "visualization", "business reasoning"],
        "secondary_skills": ["dashboarding tools", "A/B testing basics", "spreadsheet modeling"],
        "expected_topics": [
            "SQL querying", "data cleaning", "statistical reasoning",
            "visualization choices", "communicating insights", "project experience",
        ],
        "question_types": ["conceptual", "scenario", "project-based", "debugging"],
        "difficulty_guidelines": {
            "beginner": "fundamentals, definitions, basic examples (e.g. what does GROUP BY do)",
            "intermediate": "applying SQL/stats to a scenario and reasoning about the result",
            "advanced": "ambiguous business scenarios, trade-offs in metric design, data quality issues",
        },
        "project_question_strategy": (
            "Ground questions in the candidate's stated analysis projects; "
            "ask how they validated findings and what decisions their "
            "analysis influenced."
        ),
        "behavioral_overlap": ["communicating with stakeholders", "handling conflicting priorities"],
        "evaluation_focus": ["technical_accuracy", "depth", "specificity", "relevance", "clarity"],
    },
    "python_developer": {
        "role_id": "python_developer",
        "role_name": "Python Developer",
        "description": "Builds backend services, scripts, or tools primarily in Python.",
        "core_skills": [
            "Python language fundamentals", "OOP", "data structures", "APIs",
            "testing", "package/dependency management",
        ],
        "secondary_skills": ["async programming", "performance profiling", "packaging"],
        "expected_topics": ["language fundamentals", "APIs", "testing", "debugging", "project experience"],
        "question_types": ["conceptual", "debugging", "project-based", "trade-off"],
        "difficulty_guidelines": {
            "beginner": "fundamentals, definitions, basic examples (e.g. list vs tuple)",
            "intermediate": "implementation and reasoning (e.g. how would you structure this module)",
            "advanced": "performance, concurrency, architecture trade-offs",
        },
        "project_question_strategy": (
            "Ground questions in the candidate's Python projects; ask about "
            "specific design decisions and debugging experiences."
        ),
        "behavioral_overlap": ["debugging under pressure", "learning new libraries quickly"],
        "evaluation_focus": ["technical_accuracy", "depth", "specificity", "relevance", "clarity"],
    },
    "java_developer": {
        "role_id": "java_developer",
        "role_name": "Java Developer",
        "description": "Builds backend services or applications primarily in Java.",
        "core_skills": [
            "Java language fundamentals", "OOP", "collections framework",
            "exception handling", "multithreading basics", "build tools",
        ],
        "secondary_skills": ["Spring basics", "JVM fundamentals", "testing frameworks"],
        "expected_topics": ["language fundamentals", "OOP design", "concurrency basics", "project experience"],
        "question_types": ["conceptual", "debugging", "project-based", "trade-off"],
        "difficulty_guidelines": {
            "beginner": "fundamentals, definitions, basic examples (e.g. interface vs abstract class)",
            "intermediate": "implementation and reasoning about a design choice",
            "advanced": "concurrency, JVM behavior, architecture trade-offs",
        },
        "project_question_strategy": (
            "Ground questions in the candidate's Java projects; ask about "
            "class design decisions and how they handled a specific bug."
        ),
        "behavioral_overlap": ["working in a team codebase", "handling legacy code"],
        "evaluation_focus": ["technical_accuracy", "depth", "specificity", "relevance", "clarity"],
    },
}


HR_BEHAVIORAL_PROFILE: RoleProfile = {
    "role_id": "hr_behavioral",
    "role_name": "HR & Behavioral",
    "description": (
        "Evaluates soft skills and past behavior rather than technical "
        "knowledge: communication, teamwork, conflict resolution, "
        "leadership, adaptability, decision-making, and motivation."
    ),
    "core_skills": [
        "communication", "teamwork", "conflict resolution", "leadership",
        "adaptability", "decision-making", "motivation", "problem solving",
    ],
    "secondary_skills": [],
    "expected_topics": [
        "teamwork", "conflict resolution", "leadership", "adaptability",
        "decision-making", "motivation", "problem solving",
    ],
    "question_types": ["behavioral"],
    "difficulty_guidelines": {
        "beginner": "straightforward, common situations (e.g. a disagreement with a teammate)",
        "intermediate": "situations requiring judgment and trade-offs",
        "advanced": "ambiguous, high-stakes, or multi-stakeholder situations",
    },
    "project_question_strategy": (
        "Ground questions in the candidate's resume where possible (e.g. a "
        "team project, an internship), but behavioral questions can also "
        "stand alone since they ask about general past experience."
    ),
    "behavioral_overlap": [],
    "evaluation_focus": ["relevance", "communication", "star_structure", "reasoning", "specificity"],
}


TRACKS = {
    "hr_behavioral": "HR & Behavioral",
    "technical": "Technical",
}


def get_role_profile(track: str, role_id: str | None) -> RoleProfile:
    """
    Resolve the RoleProfile to use for prompt-building.
    Raises ValueError for anything the frontend shouldn't have been able
    to send in the first place (defensive backend validation).
    """
    if track == "hr_behavioral":
        return HR_BEHAVIORAL_PROFILE

    if track == "technical":
        if not role_id or role_id not in TECHNICAL_ROLES:
            raise ValueError(f"Unknown technical role_id: {role_id!r}")
        return TECHNICAL_ROLES[role_id]

    raise ValueError(f"Unknown track: {track!r}")


def list_technical_roles() -> list[dict]:
    """Small summary list for the frontend's role dropdown."""
    return [
        {"role_id": r["role_id"], "role_name": r["role_name"], "description": r["description"]}
        for r in TECHNICAL_ROLES.values()
    ]
