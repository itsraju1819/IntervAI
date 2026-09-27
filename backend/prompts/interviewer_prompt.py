"""
Prompt templates and schemas for question generation, intermediate answer analysis,
and anti-loop cross-examination in IntervAI.
"""

from typing import Any
try:
    from roles_config import RoleProfile
except ImportError:
    from backend.roles_config import RoleProfile

INTERVIEWER_SYSTEM_INSTRUCTION = """\
You are IntervAI, an elite, highly professional AI interviewer and student hiring mentor conducting a realistic mock interview.

Core Directives:
- Stay strictly in the interviewer persona during question delivery.
- Ask exactly ONE clear, focused, unambiguous question at a time.
- Never invent technologies or work experience that the candidate did not mention.
- Ground questions in the candidate's verified resume projects and claimed metrics.
- Maintain an encouraging yet rigorous evaluation bar.
- Provide a helpful coaching tip and a structured STAR or technical hint for student practice.
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
        "targeted_metric_or_project": {"type": "string"},
    },
    "required": ["question", "topic", "question_type", "tip"],
}

INTERMEDIATE_EVALUATION_SCHEMA = {
    "type": "object",
    "properties": {
        "relevance_score": {
            "type": "number",
            "description": "Score 0.0 to 10.0 for directness and alignment with the question.",
        },
        "depth_score": {
            "type": "number",
            "description": "Score 0.0 to 10.0 for technical or behavioral depth and mechanism explanation.",
        },
        "specificity_score": {
            "type": "number",
            "description": "Score 0.0 to 10.0 for citing concrete technologies, trade-offs, or measurable metrics.",
        },
        "identified_gaps": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Noticeable omissions, vague statements, hand-waving, or missing technical steps in the answer.",
        },
        "detected_claims": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific numbers, metrics, architectural choices, or tools the candidate claimed.",
        },
        "decision": {
            "type": "string",
            "enum": ["DRILL_DOWN", "ADVANCE_TOPIC", "WRAP_UP"],
            "description": "DRILL_DOWN if the answer made bold claims or left critical gaps that need probing; ADVANCE_TOPIC if sufficiently answered; WRAP_UP if interview finished.",
        },
        "reasoning": {
            "type": "string",
            "description": "A 1-2 sentence engineering justification for the decision.",
        },
    },
    "required": [
        "relevance_score",
        "depth_score",
        "specificity_score",
        "identified_gaps",
        "detected_claims",
        "decision",
        "reasoning",
    ],
}


def _format_candidate_grounding(
    resume_summary: str | None = None,
    candidate_profile: dict[str, Any] | None = None,
) -> str:
    """Formats resume and profile context including verified claims and projects."""
    blocks = []
    if candidate_profile:
        tech = candidate_profile.get("technical_stack", [])
        if tech:
            blocks.append(f"Candidate Technical Stack: {', '.join(tech[:15])}")
        seniority = candidate_profile.get("experience_level")
        if seniority:
            blocks.append(f"Seniority Level: {seniority}")
        projects = candidate_profile.get("key_projects", [])
        if projects:
            proj_descriptions = []
            for p in projects[:3]:
                p_name = p.get("project_name", "Project")
                p_metrics = ", ".join(p.get("claimed_metrics", [])) or "Functional implementation"
                p_tools = ", ".join(p.get("core_technologies", []))
                proj_descriptions.append(f"- {p_name} (Tools: {p_tools} | Claims: {p_metrics})")
            blocks.append("Verified Resume Projects & Claimed Metrics:\n" + "\n".join(proj_descriptions))

    if resume_summary and not blocks:
        blocks.append(f"Resume Summary:\n{resume_summary}")

    return "\n\n".join(blocks) if blocks else "No candidate resume provided."


def build_opening_question_prompt(
    *,
    track: str,
    role: RoleProfile,
    difficulty: str,
    resume_summary: str | None = None,
    job_description: str | None = None,
    candidate_profile: dict[str, Any] | None = None,
) -> str:
    """Builds prompt for Question 1 (Opening Question), grounded in resume claims."""
    difficulty_key = difficulty.lower()
    difficulty_guideline = role["difficulty_guidelines"].get(
        difficulty_key, role["difficulty_guidelines"].get("intermediate", "")
    )
    is_behavioral = track == "hr_behavioral"
    grounding = _format_candidate_grounding(resume_summary, candidate_profile)

    jd_section = (
        f"Target Job Description:\n{job_description}"
        if job_description
        else "No specific Job Description provided."
    )

    task_instructions = (
        "Generate a warm, professional opening behavioral interview question. "
        "Invite the candidate to introduce their background and what sparked their interest in this role."
        if is_behavioral
        else (
            f"Generate an engaging opening technical question for a {role['role_name']}. "
            "Invite them to introduce themselves and highlight a key project from their resume, "
            "focusing on the architectural decisions and technical stack they used."
        )
    )

    return f"""\
SYSTEM INSTRUCTION:
{INTERVIEWER_SYSTEM_INSTRUCTION}

ROLE: {role['role_name']} — {role['description']}
CORE SKILLS: {', '.join(role['core_skills'])}
TRACK: {"HR & Behavioral" if is_behavioral else "Technical"}
DIFFICULTY: {difficulty} — {difficulty_guideline}

CANDIDATE PROFILE & RESUME GROUNDING:
{grounding}

TARGET JOB DESCRIPTION:
{jd_section}

INTERVIEW PROGRESSION:
Question 1 (Opening Turn)

TASK:
{task_instructions}

OUTPUT FORMAT:
Conform strictly to the JSON schema:
- "question": Direct question string to the candidate.
- "topic": Short topic title (e.g. "Background & Core Architecture").
- "question_type": One of {role['question_types']}.
- "tip": Concise tip (<20 words) for answering.
- "hint": Structured bulleted guidance or STAR framework outline.
- "sample_keywords": 2-4 keywords the candidate should mention.
- "targeted_metric_or_project": Name of the project or metric referenced (if any).
"""


def build_intermediate_analysis_prompt(
    *,
    track: str,
    role: RoleProfile,
    difficulty: str,
    question: str,
    answer: str,
    current_topic: str,
    followup_count: int,
) -> str:
    """Builds prompt for intermediate structured evaluation of the candidate's last answer."""
    return f"""\
You are an expert interview evaluator analyzing a candidate's answer to determine the next interview step.

ROLE: {role['role_name']}
TRACK: {track}
DIFFICULTY: {difficulty}
CURRENT TOPIC: {current_topic}
CURRENT TOPIC FOLLOW-UP COUNT: {followup_count} of 2 max allowed

INTERVIEW QUESTION ASKED:
"{question}"

CANDIDATE'S ANSWER:
"{answer}"

INSTRUCTIONS:
1. Score relevance_score (0.0 to 10.0): Did they directly answer what was asked?
2. Score depth_score (0.0 to 10.0): Did they explain internal mechanisms, trade-offs, or concrete architecture?
3. Score specificity_score (0.0 to 10.0): Did they cite concrete metrics, specific tools, or real scenarios rather than vague generalities?
4. Extract identified_gaps: 1-3 specific omissions, unanswered aspects, or technical vagueness.
5. Extract detected_claims: Any metrics, performance improvements, tools, or architectural assertions made.
6. Make a recommendation decision:
   - "DRILL_DOWN": If the candidate made specific claims that should be verified or had glaring gaps/vagueness on this topic, AND followup_count < 2.
   - "ADVANCE_TOPIC": If the answer is reasonably thorough, or if the topic has been sufficiently explored.
   - "WRAP_UP": If the interview is concluding.
7. Provide brief reasoning.

Return strictly JSON matching the required schema.
"""


def build_drilldown_question_prompt(
    *,
    track: str,
    role: RoleProfile,
    difficulty: str,
    question_number: int,
    total_questions: int,
    current_topic: str,
    followup_count: int,
    last_question: str,
    last_answer: str,
    identified_gaps: list[str],
    detected_claims: list[str],
    candidate_profile: dict[str, Any] | None = None,
) -> str:
    """Builds prompt for generating a cross-examination question probing claims or gaps."""
    grounding = _format_candidate_grounding(candidate_profile=candidate_profile)
    gaps_str = "\n".join(f"- {g}" for g in identified_gaps) if identified_gaps else "- General depth and technical trade-offs"
    claims_str = "\n".join(f"- {c}" for c in detected_claims) if detected_claims else "- Candidate's stated implementation"

    return f"""\
SYSTEM INSTRUCTION:
{INTERVIEWER_SYSTEM_INSTRUCTION}

ROLE: {role['role_name']}
TRACK: {track}
DIFFICULTY: {difficulty}
CURRENT TOPIC: {current_topic} (Follow-up {followup_count} of 2)
QUESTION TURN: {question_number} of {total_questions}

CANDIDATE RESUME CONTEXT:
{grounding}

PREVIOUS QUESTION:
"{last_question}"

CANDIDATE'S PREVIOUS ANSWER:
"{last_answer}"

IDENTIFIED GAPS IN THEIR ANSWER:
{gaps_str}

CLAIMS OR TECHNOLOGIES DETECTED:
{claims_str}

TASK:
Generate a direct, focused cross-examination follow-up question.
Do NOT repeat the previous question.
Probe specifically into the identified gaps or cross-examine their claims:
- If they made a performance or architecture claim, ask HOW they measured it, what trade-offs occurred, or what edge cases arose.
- If their answer was vague, ask for the exact mechanism, implementation step, or failure mode.
Ensure the tone is professional, investigative, and constructive.

OUTPUT FORMAT:
Conform strictly to the QUESTION_RESPONSE_SCHEMA JSON format.
"""


def build_advance_question_prompt(
    *,
    track: str,
    role: RoleProfile,
    difficulty: str,
    question_number: int,
    total_questions: int,
    new_topic: str,
    topics_covered: list[str],
    qa_history: list[dict[str, Any]],
    resume_summary: str | None = None,
    job_description: str | None = None,
    candidate_profile: dict[str, Any] | None = None,
) -> str:
    """Builds prompt for advancing to a new domain topic cleanly."""
    difficulty_key = difficulty.lower()
    difficulty_guideline = role["difficulty_guidelines"].get(
        difficulty_key, role["difficulty_guidelines"].get("intermediate", "")
    )
    grounding = _format_candidate_grounding(resume_summary, candidate_profile)

    jd_section = (
        f"Target Job Description Requirements:\n{job_description}"
        if job_description
        else "No specific Job Description provided."
    )

    prior_summary = "\n".join(
        f"Q{i+1}: {qa.get('question', '')[:100]}... [Answered]"
        for i, qa in enumerate(qa_history[-3:])
    )

    return f"""\
SYSTEM INSTRUCTION:
{INTERVIEWER_SYSTEM_INSTRUCTION}

ROLE: {role['role_name']} — {role['description']}
TRACK: {track}
DIFFICULTY: {difficulty} — {difficulty_guideline}

NEW TARGET TOPIC: {new_topic}
TOPICS ALREADY COVERED: {', '.join(topics_covered) if topics_covered else 'None'}
QUESTION TURN: {question_number} of {total_questions}

CANDIDATE RESUME CONTEXT:
{grounding}

TARGET JOB DESCRIPTION:
{jd_section}

RECENT QUESTIONS COVERED:
{prior_summary or 'Opening question'}

TASK:
Advance the interview by formulating a fresh, high-impact question strictly targeting the NEW TOPIC: "{new_topic}".
1. Test their understanding of this competency at the {difficulty} level.
2. Ground the scenario in real-world engineering or behavioral challenges.
3. If they listed relevant tools or projects in their resume for this topic, reference them to personalize the question.

OUTPUT FORMAT:
Conform strictly to the QUESTION_RESPONSE_SCHEMA JSON format.
"""
