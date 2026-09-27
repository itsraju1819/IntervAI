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
    const isFallback = Boolean(data.is_fallback || data.source === "heuristic_fallback");
    const overallScore = data.overall_score || 60;
    const rating = data.rating || "Developing";
    const summary = data.summary || "You completed your mock interview session. Your responses were evaluated against core hiring criteria.";
    const categories = data.category_scores || {
        technical_accuracy: 65,
        clarity_communication: 70,
        problem_solving: 60,
        structure: 60,
    };
    const strengths = data.strengths || [
        "Directly addressed the interview questions with relevant context",
        "Demonstrated foundational understanding of core principles",
    ];
    const improvements = data.improvements || [
        "Structure responses explicitly using the STAR method (Situation, Task, Action, Result)",
        "Quantify your accomplishments (e.g. latency, scale, performance gains)",
    ];
    const qaEvaluations = data.question_evaluations || [];

    // Animate overall score
    animateScore(overallScore);

    // Diagnostic Fallback Banner Handling
    const diagnosticBanner = document.getElementById("diagnosticBanner");
    const diagnosticBannerMsg = document.getElementById("diagnosticBannerMsg");
    const sourceBadge = document.getElementById("sourceBadge");
    const evalSource = document.getElementById("evalSource");

    if (diagnosticBanner) {
        if (isFallback) {
            diagnosticBanner.style.display = "flex";
            if (diagnosticBannerMsg) {
                diagnosticBannerMsg.textContent = data.message || "AI evaluation service could not be reached. Local heuristic evaluation applied.";
            }
            if (sourceBadge) {
                sourceBadge.textContent = "⚠️ Heuristic / Diagnostic Estimate";
                sourceBadge.style.background = "#fef3c7";
                sourceBadge.style.color = "#92400e";
            }
            if (evalSource) evalSource.textContent = "Heuristic Estimator";
        } else {
            diagnosticBanner.style.display = "none";
            if (sourceBadge) {
                sourceBadge.textContent = data.source === "gemini" ? "✨ Gemini AI Evaluated" : "Adaptive AI Scorecard";
                sourceBadge.style.background = "";
                sourceBadge.style.color = "";
            }
            if (evalSource) evalSource.textContent = data.source === "gemini" ? "Gemini 2.5 Flash AI" : "IntervAI Evaluator";
        }
    }

    // Rating & Summary
    const ratingStatus = document.getElementById("ratingStatus");
    const summaryText = document.getElementById("summaryText");

    if (ratingStatus) ratingStatus.textContent = rating;
    if (summaryText) summaryText.textContent = summary;

    // Speech Delivery Analytics
    renderSpeechDelivery(data);

    // STAR Method Checklist
    renderStarBreakdown(data.star_breakdown);

    // Recruiter Model Rewrite
    renderAnswerRewrite(data.weakest_answer_rewrite);

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
                const delivery = (rawAnswers[idx] && rawAnswers[idx].delivery_metrics) || item.delivery_metrics;
                let deliveryBadge = "";
                if (delivery && delivery.wpm) {
                    deliveryBadge = `<span style="font-size:11px; font-weight:700; background:#e0f2fe; color:#0369a1; padding:2px 8px; border-radius:6px; margin-left:8px;">⏱️ ${delivery.wpm} WPM • ${delivery.filler_count || 0} Fillers</span>`;
                }

                return `
                <div class="qa-card">
                    <div class="qa-header">
                        <div class="qa-question">Q${idx + 1}: ${escapeHtml(item.question)} ${deliveryBadge}</div>
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

function renderSpeechDelivery(data) {
    const avgWpmEl = document.getElementById("speechAvgWpm");
    const fillerCountEl = document.getElementById("speechFillerCount");
    const clarityScoreEl = document.getElementById("speechClarityScore");
    const summaryTextEl = document.getElementById("speechDeliverySummaryText");
    const pacingPill = document.getElementById("deliveryPacingPill");

    const wpm = data.average_wpm !== null && data.average_wpm !== undefined ? data.average_wpm : null;
    const fillers = data.total_filler_words !== null && data.total_filler_words !== undefined ? data.total_filler_words : 0;

    if (avgWpmEl) avgWpmEl.textContent = wpm ? `${Math.round(wpm)}` : "--";
    if (fillerCountEl) fillerCountEl.textContent = fillers;

    let pacingText = "Optimal Cadence";
    let pacingClass = "delivery-status-pill";

    if (wpm) {
        if (wpm < 110) {
            pacingText = "Deliberate / Slow Pace";
            if (clarityScoreEl) clarityScoreEl.textContent = "Deliberate";
        } else if (wpm > 175) {
            pacingText = "Fast / Rushed Cadence";
            if (clarityScoreEl) clarityScoreEl.textContent = "Rapid";
        } else {
            pacingText = "Optimal (120-160 WPM)";
            if (clarityScoreEl) clarityScoreEl.textContent = "Optimal";
        }
    } else {
        if (clarityScoreEl) clarityScoreEl.textContent = "Text Mode";
    }

    if (pacingPill) {
        pacingPill.textContent = pacingText;
    }

    if (summaryTextEl) {
        summaryTextEl.textContent = data.speech_delivery_summary || (
            wpm
                ? `Candidate spoke at an average of ${Math.round(wpm)} words per minute with ${fillers} filler words detected. Maintain clear pauses to structure complex technical thoughts.`
                : "Responses submitted via text input. Practice voice mode to unlock verbal delivery pacing and filler-word tracking."
        );
    }
}

function renderStarBreakdown(star) {
    if (!star) return;

    function setStep(stepId, checkId, isPass) {
        const stepEl = document.getElementById(stepId);
        const checkEl = document.getElementById(checkId);
        if (!stepEl || !checkEl) return;

        if (isPass) {
            stepEl.className = "star-step checked";
            checkEl.textContent = "✓";
        } else {
            stepEl.className = "star-step missing";
            checkEl.textContent = "⚠️";
        }
    }

    setStep("starSituationStep", "starSituationCheck", star.situation);
    setStep("starTaskStep", "starTaskCheck", star.task);
    setStep("starActionStep", "starActionCheck", star.action);
    setStep("starResultStep", "starResultCheck", star.result);

    const feedbackText = document.getElementById("starFeedbackText");
    if (feedbackText && star.feedback) {
        feedbackText.textContent = star.feedback;
    }
}

function renderAnswerRewrite(rewrite) {
    const card = document.getElementById("answerRewriteCard");
    if (!card) return;

    if (!rewrite) {
        card.style.display = "none";
        return;
    }

    card.style.display = "block";
    const qText = document.getElementById("rewriteQuestionText");
    const origAns = document.getElementById("rewriteOriginalAnswer");
    const critiqueNote = document.getElementById("rewriteCritiqueNote");
    const modelAns = document.getElementById("rewriteModelAnswer");

    if (qText) qText.textContent = rewrite.question || "Selected Interview Question";
    if (origAns) origAns.textContent = rewrite.original_answer || "[No answer provided]";
    if (critiqueNote) critiqueNote.textContent = `💡 Recruiter Critique: ${rewrite.critique || "Add clear STAR structure and quantifiable results."}`;
    if (modelAns) modelAns.textContent = rewrite.rewritten_answer || "Optimized model answer...";
}

function setCategory(textId, barId, score) {
    const val = Math.min(100, Math.max(0, score || 70));
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
    const roleKeywords = [
        "code", "data", "api", "database", "system", "performance", "testing",
        "frontend", "backend", "python", "java", "sql", "model", "pipeline",
        "debug", "architecture", "scale", "team", "communication", "lead", "action"
    ];
    const scores = [];
    const qaEvals = answers.map((qa, i) => {
        const ans = (qa.answer || "").trim();
        const words = ans ? ans.split(/\s+/).filter(Boolean).length : 0;
        const lower = ans.toLowerCase();
        let score = 25;
        let feedback = "No answer was provided. Practice answering aloud with real examples.";
        if (words === 0) {
            score = 25;
            feedback = "No answer was provided. Practice answering aloud with real examples.";
        } else if (words < 15) {
            score = 55;
            feedback = "Answer was too brief. Elaborate with specific details and context.";
        } else if (words < 40) {
            const matches = roleKeywords.filter((k) => lower.includes(k)).length;
            score = Math.min(80, 65 + matches * 3);
            feedback = "Good foundation. Expand on your specific methodology, trade-offs, and results.";
        } else if (words < 100) {
            const matches = roleKeywords.filter((k) => lower.includes(k)).length;
            score = Math.min(92, 75 + matches * 2);
            feedback = "Strong and well-articulated response with relevant details and logical flow.";
        } else {
            const matches = roleKeywords.filter((k) => lower.includes(k)).length;
            score = Math.min(95, 80 + matches * 2);
            feedback = "Comprehensive and thorough response demonstrating clear subject familiarity.";
        }
        scores.push(score);
        return {
            question: qa.question || `Question ${i + 1}`,
            score: score,
            feedback: feedback,
            delivery_metrics: qa.delivery_metrics || null,
        };
    });

    const avgScore = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 55;
    let rating = "Needs Preparation";
    if (avgScore >= 85) rating = "Interview Ready";
    else if (avgScore >= 75) rating = "Very Good";
    else if (avgScore >= 65) rating = "Competent";
    else if (avgScore >= 50) rating = "Developing";

    return {
        is_fallback: true,
        evaluation_status: "evaluator_unreachable",
        message: "AI evaluation service could not be reached. Local heuristic evaluation applied.",
        overall_score: avgScore,
        rating: rating,
        summary: `You completed your ${roleName} practice session (${difficulty} level). Local heuristic evaluation applied.`,
        category_scores: {
            technical_accuracy: Math.min(100, Math.max(40, avgScore + 1)),
            clarity_communication: Math.min(100, Math.max(45, avgScore + 2)),
            problem_solving: Math.min(100, Math.max(40, avgScore - 2)),
            structure: Math.min(100, Math.max(40, avgScore - 1)),
        },
        strengths: [
            `Demonstrated relevant core competencies for ${roleName}`,
            "Maintained a professional, coherent tone across responses",
            "Directly answered interview questions with contextual examples",
        ],
        improvements: [
            "Use concrete metrics and outcomes (e.g. latency reduced, users supported) to quantify your work",
            "Structure situational examples using the STAR method (Situation, Task, Action, Result)",
        ],
        question_evaluations: qaEvals,
        star_breakdown: {
            situation: true,
            task: true,
            action: false,
            result: false,
            feedback: "Practice articulating specific technical Actions and quantifiable Results.",
        },
        weakest_answer_rewrite: {
            question: answers[0]?.question || "Technical Question",
            original_answer: answers[0]?.answer || "[No answer provided]",
            critique: "Response lacked structured STAR articulation and measurable technical outcomes.",
            rewritten_answer: `[Situation] In my ${roleName} project, our system needed to handle increased request volume without latency spikes.\n[Task] My goal was to restructure backend queries and implement reliable response caching.\n[Action] I introduced asynchronous handlers, indexed high-traffic columns in the database, and integrated Redis caching for read queries.\n[Result] This improved response times by 35% and maintained 99.9% uptime under peak load testing.`,
        },
        source: "heuristic_fallback",
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
