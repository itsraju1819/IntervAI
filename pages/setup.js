// ========================================
// IntervAI - Interview Setup & JD Alignment
// ========================================

// Elements
const setupForm = document.getElementById("setupForm");
const roleSection = document.getElementById("roleSection");
const roleSelect = document.getElementById("role");
const resumeInput = document.getElementById("resume");
const uploadArea = document.getElementById("uploadArea");
const uploadTitle = document.getElementById("uploadTitle");
const uploadText = document.getElementById("uploadText");
const fileSelected = document.getElementById("fileSelected");
const startInterviewBtn = document.getElementById("startInterviewBtn");
const setupError = document.getElementById("setupError");

// Job Description & Presets
const jobDescriptionInput = document.getElementById("jobDescription");
const jdMatchInsight = document.getElementById("jdMatchInsight");
const matchPercentage = document.getElementById("matchPercentage");
const matchedSkillsList = document.getElementById("matchedSkillsList");
const missingSkillsList = document.getElementById("missingSkillsList");
const enableHintsCheck = document.getElementById("enableHintsCheck");

// AI Status & Key Elements
const aiStatusDot = document.getElementById("aiStatusDot");
const aiStatusTitle = document.getElementById("aiStatusTitle");
const toggleApiKeyBtn = document.getElementById("toggleApiKeyBtn");
const apiKeySection = document.getElementById("apiKeySection");
const geminiApiKeyInput = document.getElementById("geminiApiKeyInput");
const saveApiKeyBtn = document.getElementById("saveApiKeyBtn");
const apiKeyMsg = document.getElementById("apiKeyMsg");

let uploadedResumeSummary = null;
let uploadedResumeSkills = [];
let jdDebounceTimer = null;

// ========================================
// STUDENT PRESETS FOR JOB DESCRIPTIONS
// ========================================

const JD_PRESETS = {
    fullstack: `Target: Full-Stack Developer Intern / Junior
Responsibilities:
- Build user interfaces using React, JavaScript, HTML5, CSS3, and state management.
- Develop backend RESTful APIs with Python (FastAPI/Django) or Node.js/Express.
- Work with relational databases (PostgreSQL/MySQL) and MongoDB.
- Write unit tests, manage version control with Git/GitHub, and implement Docker containerization.
Requirements: Experience with React, Node.js or Python, SQL, REST APIs, Git, and basic cloud deployment.`,

    ml: `Target: Junior Machine Learning Engineer
Responsibilities:
- Build, evaluate, and fine-tune machine learning and deep learning models with PyTorch or TensorFlow.
- Perform exploratory data analysis, data cleaning, feature engineering, and address class imbalance.
- Monitor models in production, prevent data drift, and optimize latency using FastAPI inference servers.
Requirements: Proficiency in Python, Pandas, NumPy, Scikit-Learn, PyTorch, Docker, and MLOps fundamentals.`,

    analyst: `Target: Entry-Level Data Analyst
Responsibilities:
- Extract, clean, and analyze complex datasets using advanced SQL (window functions, CTEs, self-joins).
- Build automated business intelligence dashboards in Tableau or PowerBI for key performance metrics.
- Formulate hypothesis testing and interpret A/B test results for product decisions.
Requirements: Strong SQL querying, Python/Pandas data wrangling, statistical analysis, and data storytelling.`,

    python: `Target: Backend Python Developer
Responsibilities:
- Architect high-performance asynchronous microservices and RESTful APIs using FastAPI/Django.
- Design database schemas, handle indexing, query optimization, and connection pooling.
- Manage memory, multithreading/asyncio concurrency, and write automated tests with pytest.
Requirements: Python 3+, OOP design patterns, FastAPI, PostgreSQL, Docker, Redis, and pytest.`
};

document.querySelectorAll(".preset-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        const presetKey = btn.dataset.preset;
        if (presetKey === "clear") {
            jobDescriptionInput.value = "";
            jdMatchInsight.classList.add("hidden");
        } else if (JD_PRESETS[presetKey]) {
            jobDescriptionInput.value = JD_PRESETS[presetKey];
            triggerJdAnalysis();
        }
    });
});

// ========================================
// REAL-TIME JD MATCH ANALYSIS
// ========================================

jobDescriptionInput.addEventListener("input", () => {
    clearTimeout(jdDebounceTimer);
    jdDebounceTimer = setTimeout(triggerJdAnalysis, 500);
});

async function triggerJdAnalysis() {
    const jdText = (jobDescriptionInput.value || "").trim();
    if (!jdText) {
        jdMatchInsight.classList.add("hidden");
        return;
    }

    try {
        const res = await fetch(`${INTERVAI_API_BASE_URL}/api/interview/analyze-jd`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                job_description: jdText,
                resume_summary: uploadedResumeSummary,
                resume_skills: uploadedResumeSkills,
            }),
        });

        if (res.ok) {
            const data = await res.json();
            renderJdMatch(data);
        }
    } catch (e) {
        console.warn("JD analysis failed:", e);
    }
}

function renderJdMatch(data) {
    if (!data.has_jd) {
        jdMatchInsight.classList.add("hidden");
        return;
    }

    jdMatchInsight.classList.remove("hidden");
    matchPercentage.textContent = `${data.match_score}% Match`;

    // Render matched pills
    if (data.matched_skills && data.matched_skills.length > 0) {
        matchedSkillsList.innerHTML = data.matched_skills
            .map((s) => `<span class="pill-matched">✓ ${escapeHtml(s)}</span>`)
            .join("");
    } else {
        matchedSkillsList.innerHTML = '<span style="font-size: 12px; color: #64748b;">Upload resume to cross-reference</span>';
    }

    // Render missing pills
    if (data.missing_skills && data.missing_skills.length > 0) {
        missingSkillsList.innerHTML = data.missing_skills
            .map((s) => `<span class="pill-missing">⚡ ${escapeHtml(s)}</span>`)
            .join("");
    } else {
        missingSkillsList.innerHTML = '<span style="font-size: 12px; color: #166534;">Great match! All core JD skills found.</span>';
    }
}

// ========================================
// AI STATUS & API KEY MANAGEMENT
// ========================================

async function checkAIStatus() {
    try {
        const res = await fetch(`${INTERVAI_API_BASE_URL}/api/health`);
        if (!res.ok) throw new Error("Health check failed");
        const data = await res.json();
        if (data.gemini_configured) {
            if (aiStatusDot) aiStatusDot.style.background = "#10b981";
            if (aiStatusTitle) aiStatusTitle.textContent = `AI Engine: Gemini Active (${data.gemini_model})`;
            if (toggleApiKeyBtn) toggleApiKeyBtn.textContent = "Change Gemini Key";
        } else {
            if (aiStatusDot) aiStatusDot.style.background = "#f59e0b";
            if (aiStatusTitle) aiStatusTitle.textContent = "AI Engine: Standard Mode (Role Bank Active)";
            if (toggleApiKeyBtn) toggleApiKeyBtn.textContent = "Add Gemini Key";
        }
    } catch {
        if (aiStatusDot) aiStatusDot.style.background = "#94a3b8";
        if (aiStatusTitle) aiStatusTitle.textContent = "AI Engine: Offline Mode (Local Bank Active)";
    }
}
checkAIStatus();

if (toggleApiKeyBtn) {
    toggleApiKeyBtn.addEventListener("click", () => {
        if (!apiKeySection) return;
        apiKeySection.style.display = apiKeySection.style.display === "none" ? "block" : "none";
    });
}

if (saveApiKeyBtn) {
    saveApiKeyBtn.addEventListener("click", async () => {
        const key = (geminiApiKeyInput.value || "").trim();
        if (!key) {
            apiKeyMsg.style.color = "#ef4444";
            apiKeyMsg.textContent = "Please enter an API key.";
            return;
        }

        saveApiKeyBtn.disabled = true;
        saveApiKeyBtn.textContent = "Verifying...";
        apiKeyMsg.style.color = "#64748b";
        apiKeyMsg.textContent = "Connecting to Gemini...";

        try {
            const res = await fetch(`${INTERVAI_API_BASE_URL}/api/interview/config/key`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ api_key: key }),
            });
            const data = await res.json();
            if (res.ok) {
                apiKeyMsg.style.color = "#10b981";
                apiKeyMsg.textContent = "✓ Key saved! Gemini AI is now active.";
                geminiApiKeyInput.value = "";
                await checkAIStatus();
                setTimeout(() => {
                    apiKeySection.style.display = "none";
                }, 2000);
            } else {
                throw new Error(data.detail || "Failed to save key");
            }
        } catch (err) {
            apiKeyMsg.style.color = "#ef4444";
            apiKeyMsg.textContent = `Error: ${err.message}`;
        } finally {
            saveApiKeyBtn.disabled = false;
            saveApiKeyBtn.textContent = "Save Key";
        }
    });
}

// ===============================
// TRACK & DIFFICULTY SELECTION
// ===============================

function updateTrackUI() {
    const checkedTrack = document.querySelector('input[name="track"]:checked');
    if (!checkedTrack) return;

    const track = checkedTrack.value;
    if (track === "technical") {
        roleSection.classList.remove("hidden");
        roleSelect.required = true;
    } else {
        roleSection.classList.add("hidden");
        roleSelect.required = false;
    }

    document.querySelectorAll(".track-card").forEach((card) => {
        const input = card.querySelector('input[name="track"]');
        if (input && input.checked) {
            card.classList.add("selected");
        } else {
            card.classList.remove("selected");
        }
    });
}

function updateDifficultyUI() {
    document.querySelectorAll(".difficulty-card").forEach((card) => {
        const input = card.querySelector('input[name="difficulty"]');
        if (input && input.checked) {
            card.classList.add("selected");
        } else {
            card.classList.remove("selected");
        }
    });
}

document.querySelectorAll('input[name="track"]').forEach((radio) => {
    radio.addEventListener("change", updateTrackUI);
});
document.querySelectorAll('input[name="difficulty"]').forEach((radio) => {
    radio.addEventListener("change", updateDifficultyUI);
});

updateTrackUI();
updateDifficultyUI();

// ===============================
// LOAD ROLES
// ===============================

async function loadBackendRoles() {
    try {
        const res = await fetch(`${INTERVAI_API_BASE_URL}/api/interview/roles`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.technical_roles && data.technical_roles.length > 0) {
            const currentVal = roleSelect.value;
            roleSelect.innerHTML = '<option value="">Select a target role</option>';
            data.technical_roles.forEach((r) => {
                const opt = document.createElement("option");
                opt.value = r.role_id;
                opt.textContent = r.role_name;
                roleSelect.appendChild(opt);
            });
            if (currentVal) {
                roleSelect.value = currentVal;
            }
        }
    } catch {
        // Fallback default roles
    }
}
loadBackendRoles();

// ===============================
// RESUME UPLOAD
// ===============================

async function handleFileSelection(file) {
    if (!file) return;

    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
        alert("Please upload a PDF resume.");
        resumeInput.value = "";
        return;
    }

    uploadTitle.textContent = file.name;
    uploadText.textContent = "Analyzing resume...";
    fileSelected.textContent = "⏳ Extracting skills from " + file.name + "...";
    fileSelected.classList.add("show");

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch(`${INTERVAI_API_BASE_URL}/api/interview/upload-resume`, {
            method: "POST",
            body: formData,
        });

        if (response.ok) {
            const resData = await response.json();
            uploadedResumeSummary = resData.summary;
            uploadedResumeSkills = resData.skills || [];
            sessionStorage.setItem("intervaiResumeSummary", resData.summary);
            sessionStorage.setItem("intervaiResumeSkills", JSON.stringify(resData.skills));

            const skillHighlights = (resData.skills || []).slice(0, 5).join(", ");
            uploadText.textContent = skillHighlights ? `Detected skills: ${skillHighlights}` : "Resume analyzed successfully";
            fileSelected.textContent = `✓ ${file.name} analyzed (${resData.skills.length} skills found)`;

            // Re-trigger JD analysis if JD text is already filled
            if (jobDescriptionInput.value.trim()) {
                triggerJdAnalysis();
            }
        } else {
            uploadText.textContent = "PDF selected";
            fileSelected.textContent = "✓ " + file.name + " selected";
        }
    } catch (e) {
        console.warn("Resume upload endpoint unavailable:", e);
        uploadText.textContent = "PDF selected (Local)";
        fileSelected.textContent = "✓ " + file.name + " selected";
    }
}

resumeInput.addEventListener("change", function () {
    handleFileSelection(resumeInput.files[0]);
});

uploadArea.addEventListener("dragover", function (event) {
    event.preventDefault();
    uploadArea.classList.add("dragging");
});

uploadArea.addEventListener("dragleave", function () {
    uploadArea.classList.remove("dragging");
});

uploadArea.addEventListener("drop", function (event) {
    event.preventDefault();
    uploadArea.classList.remove("dragging");

    const file = event.dataTransfer.files[0];
    if (!file) return;

    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    resumeInput.files = dataTransfer.files;

    handleFileSelection(file);
});

function showSetupError(message) {
    setupError.textContent = message;
    setupError.classList.add("show");
}

function clearSetupError() {
    setupError.textContent = "";
    setupError.classList.remove("show");
}

// ===============================
// FORM SUBMISSION
// ===============================

setupForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    clearSetupError();

    const trackInput = document.querySelector('input[name="track"]:checked');
    const difficultyInput = document.querySelector('input[name="difficulty"]:checked');

    const track = trackInput ? trackInput.value : "technical";
    const roleId = track === "technical" ? roleSelect.value : null;
    const difficulty = difficultyInput ? difficultyInput.value : "Intermediate";
    const resume = resumeInput.files[0];
    const jobDescription = (jobDescriptionInput.value || "").trim();
    const enableHints = enableHintsCheck ? enableHintsCheck.checked : true;

    if (track === "technical" && !roleId) {
        alert("Please select your target role.");
        return;
    }

    localStorage.setItem("interviewTrack", track);
    localStorage.setItem("interviewRoleId", roleId || "");
    localStorage.setItem("interviewDifficulty", difficulty);
    sessionStorage.setItem("intervaiJobDescription", jobDescription);
    sessionStorage.setItem("intervaiEnableHints", enableHints ? "true" : "false");

    if (resume) {
        localStorage.setItem("resumeName", resume.name);
    } else {
        localStorage.removeItem("resumeName");
    }

    startInterviewBtn.disabled = true;
    startInterviewBtn.textContent = "Setting up interview & tailoring questions...";

    const resumeSummary = uploadedResumeSummary || sessionStorage.getItem("intervaiResumeSummary") || null;

    try {
        const response = await fetch(
            `${INTERVAI_API_BASE_URL}/api/interview/start`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    track: track,
                    role_id: roleId,
                    difficulty: difficulty,
                    resume_summary: resumeSummary,
                    job_description: jobDescription || null,
                }),
            }
        );

        if (!response.ok) {
            const errorBody = await response.json().catch(() => null);
            throw new Error(
                (errorBody && errorBody.detail) ||
                "The backend could not start the interview."
            );
        }

        const data = await response.json();

        sessionStorage.setItem("intervaiSessionId", data.session_id);
        sessionStorage.setItem("intervaiTrack", data.track);
        sessionStorage.setItem("intervaiRoleId", data.role_id || "");
        sessionStorage.setItem("intervaiRoleName", data.role_name);
        sessionStorage.setItem("intervaiDifficulty", data.difficulty);
        sessionStorage.setItem("intervaiFirstQuestion", JSON.stringify(data.question));
        sessionStorage.setItem("intervaiQuestionSource", data.source);

        window.location.href = "interview.html";
    } catch (error) {
        console.error("Failed to start interview:", error);
        showSetupError(
            "Couldn't reach the IntervAI backend. (" + error.message + ")"
        );
        startInterviewBtn.disabled = false;
        startInterviewBtn.innerHTML = "Start Mock Interview <span>→</span>";
    }
});

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
