"""
Prompt templates for question generation in IntervAI.

Centralizes all prompts used by the AI interviewer to generate
both opening and adaptive follow-up interview questions with
student-focused answer blueprints and Job Description alignment.
"""

from roles_config import RoleProfile

INTERVIEWER_SYSTEM_INSTRUCTION = """\
You are IntervAI, an elite, professional AI job interviewer and student mentor conducting a realistic mock interview.

Core Directives:
- Stay strictly in the interviewer persona during the question.
- Ask exactly ONE clear, focused question at a time.
- Never invent experience or skills that were not provided.
- Maintain a professional, encouraging yet realistic interviewer demeanor.
- Adapt your question dynamically based on candidate answers, resume projects, and target Job Description.
- Provide a helpful, constructive coaching tip and a structured STAR/technical hint for students practicing their interview skills.
- Adhere strictly to the requested difficulty level.
"""

QUESTION_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {"type": "string"},
        "topic": {"type": "string"},
        "question_type": {"type": "string"},
        "tip": {"type": "string"},
        "hint": {"type": "string"},
        "sample_keywords": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["question", "topic", "question_type", "tip"],
}


def build_opening_question_prompt(
    *,
    track: str,
    role: RoleProfile,
    difficulty: str,
    resume_summary: str | None = None,
    job_description: str | None = None,
) -> str:
    """Builds the prompt for Question 1 (Opening Question)."""
    difficulty_key = difficulty.lower()
    difficulty_guideline = role["difficulty_guidelines"].get(
        difficulty_key, role["difficulty_guidelines"].get("intermediate", "")
    )
    is_behavioral = track == "hr_behavioral"

    resume_section = (
        f"Candidate Resume Highlights:\n{resume_summary}"
        if resume_summary
        else "No resume uploaded."
    )

    jd_section = (
        f"Target Job Description Requirements:\n{job_description}\n(Align question expectations with this target job)"
        if job_description
        else "No specific Job Description provided."
    )

    task_instructions = (
        "Generate a friendly, natural opening behavioral interview question. "
        "It should welcome the candidate and ask them to introduce themselves and their career path."
        if is_behavioral
        else (
            f"Generate an opening interview question for a {role['role_name']}. "
            "It should invite the candidate to introduce themselves and highlight "
            "relevant technical projects and core competencies aligned with the role and JD."
        )
    )

    return f"""\
SYSTEM RULES
{INTERVIEWER_SYSTEM_INSTRUCTION}

ROLE
{role['role_name']} — {role['description']}
Core skills for this role: {', '.join(role['core_skills'])}

TRACK
{"HR & Behavioral" if is_behavioral else "Technical"}

DIFFICULTY
{difficulty} — {difficulty_guideline}

TARGET JOB DESCRIPTION
{jd_section}

CANDIDATE CONTEXT
{resume_section}

INTERVIEW STATE
Question 1 of 5 (Opening Question).

TASK
{task_instructions}

OUTPUT FORMAT
Return a JSON object conforming to:
- "question": the interview question text spoken to the candidate.
- "topic": short topic label (e.g. "Introduction", "Core Skills").
- "question_type": one of {role['question_types']}.
- "tip": coaching tip (under 20 words) for answering well.
- "hint": (Student helper) 2-3 bullet points or STAR framework outline showing how to structure a winning response.
- "sample_keywords": 2-4 key technical or behavioral terms the student should consider mentioning.
"""


def build_next_question_prompt(
    *,
    track: str,
    role: RoleProfile,
    difficulty: str,
    question_number: int,
    total_questions: int,
    qa_history: list[dict[str, str]],
    resume_summary: str | None = None,
    job_description: str | None = None,
) -> str:
    """
    Builds the prompt for generating an adaptive follow-up question
    based on previous answers, resume context, and target Job Description.
    """
    difficulty_key = difficulty.lower()
    difficulty_guideline = role["difficulty_guidelines"].get(
        difficulty_key, role["difficulty_guidelines"].get("intermediate", "")
    )
    is_behavioral = track == "hr_behavioral"

    transcript_blocks = []
    for idx, qa in enumerate(qa_history, start=1):
        q = qa.get("question", "")
        a = (qa.get("answer") or "").strip() or "[No answer provided]"
        transcript_blocks.append(f"Q{idx}: {q}\nCandidate Answer: {a}")
    prior_transcript = "\n\n".join(transcript_blocks)

    resume_section = (
        f"Candidate Resume Highlights:\n{resume_summary}"
        if resume_summary
        else "No resume uploaded."
    )

    jd_section = (
        f"Target Job Description Requirements:\n{job_description}"
        if job_description
        else "No specific Job Description provided."
    )

    expected_topics = ", ".join(role["expected_topics"])

    task_instructions = (
        f"You are conducting Question {question_number} of {total_questions}. "
        "Review the candidate's last answer in the transcript. "
        "1. Formulate an adaptive question that either probes their technical depth on something they mentioned, "
        "tests a practical trade-off, or shifts to an uncovered requirement from the Job Description / Role profile. "
        f"2. Ensure the question tests core expectations for {role['role_name']} at {difficulty} level. "
        "3. Do NOT repeat previous questions. Advance the interview sequence smoothly."
    )

    return f"""\
SYSTEM RULES
{INTERVIEWER_SYSTEM_INSTRUCTION}

ROLE
{role['role_name']} — {role['description']}
Expected Competencies / Topics: {expected_topics}

TRACK
{"HR & Behavioral" if is_behavioral else "Technical"}

DIFFICULTY
{difficulty} — {difficulty_guideline}

TARGET JOB DESCRIPTION
{jd_section}

CANDIDATE CONTEXT
{resume_section}

INTERVIEW PROGRESSION
Question {question_number} of {total_questions}

PREVIOUS INTERVIEW TRANSCRIPT:
{prior_transcript}

TASK
{task_instructions}

OUTPUT FORMAT
Return a JSON object conforming to:
- "question": the adaptive interview question text spoken to the candidate.
- "topic": 1-3 word competency area tested.
- "question_type": one of {role['question_types']}.
- "tip": one actionable coaching tip (under 20 words).
- "hint": (Student helper) A concrete STAR breakdown or key talking points to guide their answer.
- "sample_keywords": 2-4 recommended keywords for this topic.
"""
