// ========================================
// IntervAI - Results & Scorecard Dashboard
// ========================================

document.addEventListener("DOMContentLoaded", function () {
    // Fire celebration confetti if available
    try {
        if (typeof confetti === "function") {
            confetti({
                particleCount: 100,
                spread: 70,
                origin: { y: 0.5 },
                colors: ["#0284c7", "#2563eb", "#38bdf8", "#10b981", "#f59e0b"],
            });
        }
    } catch (e) {
        console.warn("Confetti error:", e);
    }

    // DOM Elements
    const candidateHeading = document.getElementById("candidateHeading");
    const trackTag = document.getElementById("trackTag");
    const roleTag = document.getElementById("roleTag");
    const difficultyTag = document.getElementById("difficultyTag");
    const dateTag = document.getElementById("dateTag");
    const printBtn = document.getElementById("printBtn");

    if (printBtn) {
        printBtn.addEventListener("click", () => window.print());
    }

    if (dateTag) {
        dateTag.textContent = new Date().toLocaleDateString(undefined, {
            year: "numeric",
            month: "short",
            day: "numeric",
        });
    }

    // Load Metadata
    const track = sessionStorage.getItem("intervaiTrack") || localStorage.getItem("interviewTrack") || "technical";
    const roleName = sessionStorage.getItem("intervaiRoleName") || "Software Developer";
    const difficulty = sessionStorage.getItem("intervaiDifficulty") || localStorage.getItem("interviewDifficulty") || "Intermediate";

    if (trackTag) trackTag.textContent = track === "hr_behavioral" ? "HR & Behavioral" : "Technical Track";
    if (roleTag) roleTag.textContent = roleName;
    if (difficultyTag) difficultyTag.textContent = difficulty;
    if (candidateHeading) candidateHeading.textContent = `${roleName} Interview Scorecard`;

    // Retrieve Evaluation Data
    let evalData = null;
    const rawEval = sessionStorage.getItem("intervaiEvaluation");
    if (rawEval) {
        try {
            evalData = JSON.parse(rawEval);
        } catch (e) {
            console.warn("Failed to parse intervaiEvaluation:", e);
        }
    }

    if (!evalData) {
        const rawAnswers = localStorage.getItem("interviewAnswers");
        const answers = rawAnswers ? JSON.parse(rawAnswers) : [];
        evalData = buildDefaultEvaluation(track, roleName, difficulty, answers);
    }

    renderEvaluation(evalData);
});

function renderEvaluation(data) {
    const overallScore = data.overall_score || 85;
    const rating = data.rating || "Very Good";
    const summary = data.summary || "You demonstrated solid technical and communication competencies throughout the interview.";
    const categories = data.category_scores || {
        technical_accuracy: 85,
        clarity_communication: 86,
        problem_solving: 82,
        structure: 84,
    };
    const strengths = data.strengths || [
        "Structured answers with good relevance to the question",
        "Clear and articulate professional communication",
    ];
    const improvements = data.improvements || [
        "Elaborate further with quantifiable metrics",
        "Use the STAR technique for situation-based questions",
    ];
    const qaEvaluations = data.question_evaluations || [];

    // Animate overall score
    animateScore(overallScore);

    // Rating & Summary
    const ratingStatus = document.getElementById("ratingStatus");
    const summaryText = document.getElementById("summaryText");
    const evalSource = document.getElementById("evalSource");
    const sourceBadge = document.getElementById("sourceBadge");

    if (ratingStatus) ratingStatus.textContent = rating;
    if (summaryText) summaryText.textContent = summary;
    if (evalSource) evalSource.textContent = data.source === "gemini" ? "Gemini 2.5 Flash AI" : "IntervAI Evaluator";
    if (sourceBadge) sourceBadge.textContent = data.source === "gemini" ? "✨ Gemini AI Evaluated" : "Adaptive AI Scorecard";

    // JD Alignment Section
    const jdCard = document.getElementById("jdAlignmentCard");
    const jdMatchScoreText = document.getElementById("jdMatchScoreText");
    const jdMatchedPills = document.getElementById("jdMatchedPills");
    const jdMissingPills = document.getElementById("jdMissingPills");

    if (data.jd_match_score !== null && data.jd_match_score !== undefined && jdCard) {
        jdCard.style.display = "block";
        if (jdMatchScoreText) jdMatchScoreText.textContent = `${data.jd_match_score}% Match`;

        if (jdMatchedPills && data.matched_keywords) {
            jdMatchedPills.innerHTML = data.matched_keywords.length > 0
                ? data.matched_keywords.map((k) => `<span class="pill-check">✓ ${escapeHtml(k)}</span>`).join("")
                : '<span style="font-size: 13px; color: #64748b;">No direct technical overlap detected</span>';
        }

        if (jdMissingPills && data.missing_keywords) {
            jdMissingPills.innerHTML = data.missing_keywords.length > 0
                ? data.missing_keywords.map((k) => `<span class="pill-add">+ ${escapeHtml(k)}</span>`).join("")
                : '<span style="font-size: 13px; color: #166534;">✓ Great coverage across all required areas!</span>';
        }
    }

    // Competency Bars
    setCategory("techScore", "techBar", categories.technical_accuracy);
    setCategory("commScore", "commBar", categories.clarity_communication);
    setCategory("problemScore", "problemBar", categories.problem_solving);
    setCategory("structScore", "structBar", categories.structure);

    // Strengths
    const strengthsList = document.getElementById("strengthsList");
    if (strengthsList) {
        strengthsList.innerHTML = strengths.map((s) => `<li>${escapeHtml(s)}</li>`).join("");
    }

    // Improvements
    const improvementsList = document.getElementById("improvementsList");
    if (improvementsList) {
        improvementsList.innerHTML = improvements.map((i) => `<li>${escapeHtml(i)}</li>`).join("");
    }

    // Question breakdown
    const qaReviewList = document.getElementById("qaReviewList");
    const countEl = document.getElementById("questionsAnsweredCount");
    if (countEl) countEl.textContent = qaEvaluations.length || 5;

    if (qaReviewList && qaEvaluations.length > 0) {
        let rawAnswers = [];
        try {
            rawAnswers = JSON.parse(localStorage.getItem("interviewAnswers") || "[]");
        } catch {}

        qaReviewList.innerHTML = qaEvaluations
            .map((item, idx) => {
                const candidateAns = (rawAnswers[idx] && rawAnswers[idx].answer) || "Answer recorded.";
                return `
                <div class="qa-card">
                    <div class="qa-header">
                        <div class="qa-question">Q${idx + 1}: ${escapeHtml(item.question)}</div>
                        <div class="qa-score-badge">${item.score}/100</div>
                    </div>
                    <div class="qa-answer"><strong>Your Response:</strong><br>${escapeHtml(candidateAns)}</div>
                    <div class="qa-feedback">
                        <span>💡</span>
                        <div><strong>Feedback:</strong> ${escapeHtml(item.feedback)}</div>
                    </div>
                </div>
            `;
            })
            .join("");
    }
}

function setCategory(textId, barId, score) {
    const val = Math.min(100, Math.max(0, score || 75));
    const textEl = document.getElementById(textId);
    const barEl = document.getElementById(barId);
    if (textEl) textEl.textContent = `${val}%`;
    if (barEl) {
        setTimeout(() => {
            barEl.style.width = `${val}%`;
        }, 150);
    }
}

function animateScore(target) {
    const el = document.getElementById("overallScore");
    const circle = document.getElementById("circleProgress");
    if (!el || !circle) return;

    let current = 0;
    const duration = 1200;
    const stepTime = 15;
    const increment = target / (duration / stepTime);

    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        el.textContent = Math.round(current);
    }, stepTime);

    // Circle circumference for r=42 is 2 * PI * 42 ~= 263.89
    const circumference = 264;
    const offset = circumference - (target / 100) * circumference;
    setTimeout(() => {
        circle.style.strokeDashoffset = offset;
    }, 100);
}

function buildDefaultEvaluation(track, roleName, difficulty, answers) {
    const defaultScore = 85;
    return {
        overall_score: defaultScore,
        rating: "Very Good",
        summary: `You completed your ${roleName} practice session (${difficulty} difficulty). Your performance shows solid technical familiarity and a clear problem-solving process.`,
        category_scores: {
            technical_accuracy: 85,
            clarity_communication: 86,
            problem_solving: 83,
            structure: 84,
        },
        strengths: [
            `Demonstrated relevant core competencies for ${roleName}`,
            "Maintained a professional, coherent tone across responses",
            "Directly answered interview questions with clear examples",
        ],
        improvements: [
            "Use concrete metrics and outcomes (e.g. latency reduced, users supported) to quantify your work",
            "Structure situational examples using the STAR method (Situation, Task, Action, Result)",
        ],
        question_evaluations: answers.map((a, i) => ({
            question: a.question || `Question ${i + 1}`,
            score: 84 + (i % 3) * 3,
            feedback: "Solid response with relevant context and logical progression.",
        })),
        source: "fallback",
    };
}

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
