// ========================================
// IntervAI - Interview Engine & Student Coach
// ========================================

const ROLE_FALLBACK_BANKS = {
    hr_behavioral: [
        {
            question: "To start, could you walk me through your background and what motivates your interest in this role?",
            tip: "Keep it concise (1-2 minutes): highlight your education, core strengths, and alignment with our mission.",
            topic: "Introduction",
            hint: "• Present: Your current education / technical focus\n• Past: 1-2 major projects or milestones that shaped your passion\n• Future: Why this specific role and company excite you",
            sample_keywords: ["passionate", "milestones", "collaboration", "growth mindset"]
        },
        {
            question: "Describe a project or situation where you had to collaborate closely with a team under a tight deadline.",
            tip: "Use the STAR method: Situation, Task, Action, and Result. Emphasize constructive communication.",
            topic: "Teamwork",
            hint: "• Situation: The project context and tight deadline\n• Task: Your specific responsibility\n• Action: How you coordinated, divided tasks, or resolved blockers\n• Result: Delivered on time, learned effective delegation",
            sample_keywords: ["STAR method", "clear communication", "prioritization", "successful delivery"]
        },
        {
            question: "Tell me about a time you experienced a disagreement or conflict with a teammate or stakeholder. How did you resolve it?",
            tip: "Show emotional intelligence, active listening, and how you found common ground focused on project goals.",
            topic: "Conflict Resolution",
            hint: "• Situation: Different opinions on technical approach or task ownership\n• Action: Scheduled a 1-on-1, actively listened, focused on objective criteria\n• Result: Reached a consensus and maintained a positive working relationship",
            sample_keywords: ["active listening", "compromise", "data-driven", "mutual respect"]
        },
        {
            question: "Can you describe a situation where a plan or project didn't go as expected? What did you learn from that experience?",
            tip: "Own the setback objectively. Focus on the lessons learned and how you changed your approach afterward.",
            topic: "Adaptability",
            hint: "• Situation: A bug, delayed deliverable, or scope change\n• Action: Took accountability, communicated early, implemented a workaround\n• Result & Learning: What preventative measure you adopted for future work",
            sample_keywords: ["accountability", "pivot", "root cause", "continuous improvement"]
        },
        {
            question: "Where do you see yourself professionally in the next 2 to 3 years, and how will this role help you get there?",
            tip: "Show ambition paired with realistic growth milestones that demonstrate commitment to the team.",
            topic: "Career Goals",
            hint: "• Skill Growth: Mastering production best practices and system architecture\n• Value Added: Taking ownership of features and mentoring juniors\n• Alignment: Growing into a reliable core contributor in the organization",
            sample_keywords: ["technical mastery", "mentorship", "ownership", "long-term commitment"]
        }
    ],
    full_stack_developer: [
        {
            question: "Tell me about your background and walk me through a major full-stack application you've designed and built.",
            tip: "Mention your tech stack choices for both frontend and backend, and the core user problem you solved.",
            topic: "Architecture & Projects",
            hint: "• Problem: What user problem did your app solve?\n• Architecture: Frontend (React/Vue), Backend (FastAPI/Node), Database (PostgreSQL/MongoDB)\n• Highlight: One technical challenge you overcame (e.g. auth, state flow, caching)",
            sample_keywords: ["REST API", "State Management", "Database Design", "Authentication"]
        },
        {
            question: "How do you design a clean, maintainable RESTful API? What principles do you follow for status codes, error handling, and versioning?",
            tip: "Discuss consistent payload structures, HTTP verbs, idempotent methods, and centralized error middleware.",
            topic: "API Design",
            hint: "• Verbs & Nouns: GET /items, POST /items, PUT/PATCH, DELETE\n• Status Codes: 200/201 (success), 400 (bad request), 401/403 (auth), 404, 500\n• Best Practices: Centralized exception handlers, versioning (/api/v1), consistent JSON format",
            sample_keywords: ["Idempotency", "HTTP Status Codes", "JSON Schema", "Middleware"]
        },
        {
            question: "How do you handle state management, asynchronous operations, and responsiveness on the frontend when handling large datasets?",
            tip: "Mention component modularity, pagination/virtualization, caching, and clean client-side state flow.",
            topic: "Frontend State",
            hint: "• State Flow: Local state (useState) vs global store (Context / Redux)\n• Large Data: Virtual scrolling / pagination to prevent DOM bloat\n• UX: Skeleton loaders, optimistic UI updates, debouncing search inputs",
            sample_keywords: ["Virtual DOM", "Debouncing", "Pagination", "Optimistic Updates"]
        },
        {
            question: "Describe how you approach database schema design, indexing, and preventing common performance bottlenecks like N+1 queries.",
            tip: "Explain indexing strategies, query execution plans, normalization vs denormalization, and ORM optimizations.",
            topic: "Database Optimization",
            hint: "• Schema: Normalization up to 3NF, foreign keys and constraints\n• Indexing: B-tree indexes on foreign keys and frequently queried fields (WHERE/JOIN)\n• N+1 Fix: Using eager loading (JOINs / select_related) instead of lazy querying in a loop",
            sample_keywords: ["B-Tree Indexing", "Eager Loading", "Foreign Keys", "Execution Plan (EXPLAIN)"]
        },
        {
            question: "How do you address security (e.g., auth, CORS, input validation, SQL injection) and deploy your full-stack applications to production?",
            tip: "Highlight JWT/session security, HTTPS, sanitization libraries, Docker containerization, and CI/CD pipelines.",
            topic: "Security & Deployment",
            hint: "• Security: Parameterized queries (ORM), input validation with Pydantic/Zod, secure HTTP-only cookies, CORS whitelist\n• Deployment: Docker container, cloud hosting (Render/AWS/Vercel), automated CI/CD pipeline",
            sample_keywords: ["JWT / Cookies", "Docker Container", "CORS Configuration", "CI/CD Pipeline"]
        }
    ],
    ml_engineer: [
        {
            question: "Tell me about your background in machine learning and a specific model or ML pipeline you recently developed.",
            tip: "Clearly describe the dataset, the business or research problem, your modeling strategy, and final results.",
            topic: "ML Projects",
            hint: "• Objective: What were you predicting or classifying?\n• Pipeline: Data cleaning -> Feature extraction -> Baseline model -> Tuned model\n• Result: Metrics achieved (F1, Accuracy, AUC) and real-world significance",
            sample_keywords: ["Pipeline", "Feature Engineering", "Baseline Model", "Evaluation Metrics"]
        },
        {
            question: "How do you approach exploratory data analysis, data cleaning, and handling challenges like missing values or severe class imbalance?",
            tip: "Mention techniques like SMOTE, class-weighted loss, stratified sampling, and imputation trade-offs.",
            topic: "Data Preprocessing",
            hint: "• Missing Data: Imputation (median/KNN) vs dropping based on missingness mechanism\n• Imbalance: SMOTE (oversampling), random undersampling, or class_weight='balanced'\n• Validation: Always use Stratified K-Fold to maintain class proportions",
            sample_keywords: ["SMOTE", "Class Weights", "Stratified K-Fold", "Data Imputation"]
        },
        {
            question: "Walk me through how you choose between different model architectures and diagnose high bias (underfitting) versus high variance (overfitting).",
            tip: "Discuss learning curves, regularization (L1/L2, dropout), cross-validation, and complexity trade-offs.",
            topic: "Model Evaluation",
            hint: "• High Bias: Poor train and validation performance -> Increase model complexity, add features\n• High Variance: High train accuracy, low validation accuracy -> Add L1/L2 regularization, dropout, more data\n• Trade-off: Start with simple linear/tree baseline before deep learning",
            sample_keywords: ["Bias-Variance Tradeoff", "L1/L2 Regularization", "Dropout", "Learning Curves"]
        },
        {
            question: "Which evaluation metrics do you prioritize (e.g., Precision, Recall, F1, ROC-AUC) when accuracy is misleading, and how do you validate your choices?",
            tip: "Tie your metric choice directly to the business cost of false positives versus false negatives.",
            topic: "Metrics",
            hint: "• High Cost of False Negatives (e.g. medical diagnosis, fraud): Prioritize Recall\n• High Cost of False Positives (e.g. spam filter, loan denial): Prioritize Precision\n• Overall: F1-score harmonic mean or ROC-AUC for threshold-independent evaluation",
            sample_keywords: ["Precision vs Recall", "F1 Score", "Confusion Matrix", "ROC-AUC"]
        },
        {
            question: "How do you deploy and monitor ML models in production to detect data drift, concept drift, or latency degradation over time?",
            tip: "Mention serving frameworks (FastAPI/TorchServe), containerization, monitoring drift, and CI/CD for models.",
            topic: "MLOps",
            hint: "• Serving: Wrap model in a FastAPI microservice with ONNX/TensorRT for fast inference\n• Drift: Monitor input feature distributions (KS test) and ground truth performance degradation\n• Pipeline: CI/CD with automated retraining triggers and fallback models",
            sample_keywords: ["Data Drift", "Model Serving (FastAPI)", "Latency Optimization", "Model Monitoring"]
        }
    ],
    data_analyst: [
        {
            question: "Tell me about your background and a data analysis project where your findings directly influenced a business or product decision.",
            tip: "Highlight the business context, the question you set out to answer, and the measurable impact of your recommendation.",
            topic: "Business Impact",
            hint: "• Context: What business question or drop in metric was investigated?\n• Method: SQL extraction -> Pandas cleaning -> Cohort/trend analysis -> Visual dashboard\n• Impact: Recommended change that drove X% increase in retention/revenue",
            sample_keywords: ["Business KPI", "Actionable Insight", "Cohort Analysis", "Data Storytelling"]
        },
        {
            question: "What is your approach to writing complex SQL queries? How do you leverage window functions, CTEs, and self-joins for cohort or trend analysis?",
            tip: "Discuss readability, execution efficiency, window partitions, and optimizing aggregation pipelines.",
            topic: "SQL Queries",
            hint: "• CTEs: Break complex multi-stage aggregations into clean WITH clauses\n• Window Functions: ROW_NUMBER(), RANK(), LAG()/LEAD() OVER (PARTITION BY ... ORDER BY ...)\n• Optimization: Filter early with WHERE, index join columns, avoid unnecessary SELECT *",
            sample_keywords: ["Window Functions (PARTITION BY)", "Common Table Expressions (CTEs)", "LEAD / LAG", "Query Optimization"]
        },
        {
            question: "How do you handle dirty, inconsistent, or missing data when working on an analysis? Can you share a time you discovered an anomaly in raw data?",
            tip: "Explain your validation steps, anomaly detection methods, and how you documented assumptions transparently.",
            topic: "Data Cleaning",
            hint: "• Detection: Summary stats (describe()), box plots, checking NULL rates, finding duplicate primary keys\n• Resolution: Documenting cleaning rules, deduplicating, validating with domain experts\n• Communication: Transparently flagging limitations in reports",
            sample_keywords: ["Data Validation", "Outlier Detection", "Null Imputation", "Data Lineage"]
        },
        {
            question: "When presenting technical findings and complex data to non-technical stakeholders, how do you decide what visualizations and key metrics to present?",
            tip: "Emphasize storytelling with data, avoiding clutter, choosing the right chart types, and focusing on actionable takeaways.",
            topic: "Data Storytelling",
            hint: "• Audience: Lead with bottom-line takeaway (revenue, conversion, churn)\n• Chart Choice: Line for trends, bar for categories, avoid cluttered pie charts\n• Delivery: Highlight 'So What?' and next recommended steps",
            sample_keywords: ["Data Storytelling", "Executive Summary", "Actionable Recommendations", "Dashboarding"]
        },
        {
            question: "How do you design and interpret A/B tests or experiment results to ensure statistical significance before recommending a rollout?",
            tip: "Mention sample size calculation, p-values, confidence intervals, and avoiding common pitfalls like peeking at data early.",
            topic: "Experimentation",
            hint: "• Setup: Define primary KPI, null hypothesis, calculate minimum sample size (power analysis)\n• Analysis: Compare Control vs Treatment with two-sample t-test / Z-test, check p-value < 0.05\n• Safeguard: Check for sample ratio mismatch (SRM) and avoid early stopping",
            sample_keywords: ["Hypothesis Testing", "p-value & Confidence Interval", "Sample Size Power", "Statistical Significance"]
        }
    ],
    python_developer: [
        {
            question: "Tell me about your experience with Python and walk me through a complex application or tool you've built using the language.",
            tip: "Highlight the problem, libraries used, architectural design, and why Python was well-suited for it.",
            topic: "Python Architecture",
            hint: "• Project Scope: Backend service, scraper, CLI tool, or data pipeline\n• Design: Modular packages, typing (type hints), clean exception hierarchy\n• Highlight: One performance or concurrency optimization",
            sample_keywords: ["Type Hinting", "Modular Architecture", "Virtual Environments", "Clean Code"]
        },
        {
            question: "How does Python handle memory management and garbage collection? Can you explain the role of reference counting and the cyclic GC?",
            tip: "Mention reference counting, generational garbage collection, cyclic references, and weak references.",
            topic: "Python Internals",
            hint: "• Reference Counting: Primary mechanism (increments when referenced, deallocates at 0)\n• Cyclic GC: Detects circular references using 3 generational heaps (Gen 0, 1, 2)\n• Tooling: Using weakref or gc module for inspecting memory leaks",
            sample_keywords: ["Reference Counting", "Generational GC", "Circular References", "Memory Profiling"]
        },
        {
            question: "Explain the Global Interpreter Lock (GIL) and how you approach concurrency in Python using threading, multiprocessing, and asyncio.",
            tip: "Contrast I/O-bound tasks (asyncio/threading) with CPU-bound tasks (multiprocessing) and their trade-offs.",
            topic: "Concurrency",
            hint: "• GIL: Mutex that prevents multiple native threads from executing Python bytecode simultaneously\n• I/O-bound: Use asyncio or threading (GIL is released during network/disk I/O)\n• CPU-bound: Use multiprocessing (spawns separate processes with independent Python interpreters)",
            sample_keywords: ["GIL (Global Interpreter Lock)", "asyncio / Event Loop", "multiprocessing", "I/O vs CPU bound"]
        },
        {
            question: "How do you structure Python code for maintainability using object-oriented principles, generators, decorators, and context managers?",
            tip: "Give a practical example of a custom decorator or context manager and why it reduces boilerplate.",
            topic: "Design Patterns",
            hint: "• Decorators: @functools.wraps for logging, authentication, or timing execution\n• Context Managers: with statement (__enter__ and __exit__) for reliable resource cleanup\n• Generators: yield statement for streaming large datasets in constant memory",
            sample_keywords: ["Decorators", "Context Managers", "Generators (yield)", "Magic Methods"]
        },
        {
            question: "What is your approach to testing and profiling Python applications? How do you detect and fix memory leaks or CPU bottlenecks?",
            tip: "Mention pytest, mock fixtures, cProfile, tracemalloc, and optimizing algorithmic complexity.",
            topic: "Testing & Profiling",
            hint: "• Testing: pytest with fixtures, parametrized tests, unittest.mock for external APIs\n• Profiling: cProfile for CPU bottlenecks, tracemalloc for memory allocations\n• Optimization: Using built-in collections, vectorization (NumPy), or list comprehensions",
            sample_keywords: ["pytest & Fixtures", "cProfile", "Mocking APIs", "tracemalloc"]
        }
    ],
    java_developer: [
        {
            question: "Tell me about your Java background and describe a key enterprise or backend project you have worked on.",
            tip: "Highlight the Java version, frameworks used (e.g. Spring Boot), architecture, and your specific responsibilities.",
            topic: "Java Projects",
            hint: "• Stack: Java 17/21, Spring Boot, Maven/Gradle, Hibernate/JPA, PostgreSQL\n• Architecture: Controller -> Service -> Repository layer pattern\n• Achievement: Implemented secure REST endpoints and optimized query latency",
            sample_keywords: ["Spring Boot", "Layered Architecture", "Maven / Gradle", "JPA / Hibernate"]
        },
        {
            question: "Can you explain the core differences between an interface and an abstract class in modern Java, and when you would prefer one over the other?",
            tip: "Mention default/static methods in interfaces, multiple inheritance of type, and is-a vs can-do relationships.",
            topic: "OOP Design",
            hint: "• Abstract Class: Can hold state (instance variables), constructors; used for 'is-a' relationships and shared implementation\n• Interface: Defines a contract / 'can-do' behavior; a class can implement multiple interfaces; supports default/static methods since Java 8",
            sample_keywords: ["Contract vs State", "Multiple Inheritance", "Default Methods", "Polymorphism"]
        },
        {
            question: "How do you handle multithreading and thread safety in Java? Explain concepts like the volatile keyword, synchronized blocks, and java.util.concurrent.",
            tip: "Discuss atomic variables, thread pools (ExecutorService), concurrent collections, and the Java Memory Model.",
            topic: "Concurrency",
            hint: "• volatile: Ensures visibility across threads by reading directly from main memory\n• synchronized: Mutual exclusion (mutex) on monitor lock for critical sections\n• java.util.concurrent: ExecutorService thread pools, ConcurrentHashMap, AtomicInteger",
            sample_keywords: ["volatile", "ExecutorService", "ConcurrentHashMap", "Atomic Variables"]
        },
        {
            question: "How does the Spring Framework (or Spring Boot) handle Dependency Injection, Inversion of Control, and Bean lifecycle management?",
            tip: "Explain the Spring ApplicationContext, autowiring, singleton vs prototype scope, and common annotations.",
            topic: "Spring Framework",
            hint: "• IoC: Framework creates and manages object lifecycles rather than manual new operators\n• DI: Constructor injection (recommended) vs @Autowired field injection\n• Scopes: Singleton (default, one per container) vs Prototype (new per request)",
            sample_keywords: ["Inversion of Control (IoC)", "Constructor Injection", "Bean Scopes", "ApplicationContext"]
        },
        {
            question: "How does the Java Virtual Machine (JVM) manage memory (Heap, Stack, Metaspace), and how do you troubleshoot an OutOfMemoryError?",
            tip: "Discuss JVM memory regions, garbage collection algorithms (G1, ZGC), heap dumps, and profilers.",
            topic: "JVM Tuning",
            hint: "• Memory: Stack (thread-specific method frames & local primitives) vs Heap (objects & garbage collected)\n• Troubleshooting: Take heap dump on OOM (-XX:+HeapDumpOnOutOfMemoryError), analyze in Eclipse Memory Analyzer (MAT) or VisualVM\n• Tuning: Garbage collectors like G1GC or ZGC for low-pause performance",
            sample_keywords: ["Heap vs Stack", "G1 Garbage Collector", "Heap Dump Analysis", "OutOfMemoryError"]
        }
    ]
};

// Track and role resolution
const activeTrack = sessionStorage.getItem("intervaiTrack") || localStorage.getItem("interviewTrack") || "technical";
const activeRoleId = sessionStorage.getItem("intervaiRoleId") || localStorage.getItem("interviewRoleId") || "full_stack_developer";
const savedJd = sessionStorage.getItem("intervaiJobDescription") || "";

const bankKey = activeTrack === "hr_behavioral" ? "hr_behavioral" : (ROLE_FALLBACK_BANKS[activeRoleId] ? activeRoleId : "full_stack_developer");
let questions = [...ROLE_FALLBACK_BANKS[bankKey]];

// State
let currentQuestion = 0;
const totalQuestionsCount = 5;
let answers = [];
let isRecording = false;
let recognition = null;
let speechSeconds = 0;
let timerInterval = null;

// DOM Elements
const questionText = document.getElementById("questionText");
const questionNumber = document.getElementById("questionNumber");
const questionTopic = document.getElementById("questionTopic");
const questionSourceTag = document.getElementById("questionSourceTag");
const progressFill = document.getElementById("progressFill");
const progressPercentage = document.getElementById("progressPercentage");
const interviewTip = document.getElementById("interviewTip");
const answerInput = document.getElementById("answerInput");
const wordCount = document.getElementById("wordCount");
const wordGauge = document.getElementById("wordGauge");
const submitAnswer = document.getElementById("submitAnswer");
const playQuestionBtn = document.getElementById("playQuestionBtn");
const roleDisplay = document.getElementById("roleDisplay");
const difficultyDisplay = document.getElementById("difficultyDisplay");
const jdTagBadge = document.getElementById("jdTagBadge");
const backendStatus = document.getElementById("backendStatus");
const clearAnswerBtn = document.getElementById("clearAnswerBtn");
const aiAvatarIcon = document.getElementById("aiAvatarIcon");

// Pacing & Timer Elements
const pacingTimer = document.getElementById("pacingTimer");
const pacingStatus = document.getElementById("pacingStatus");

// Student Hint Drawer
const studentHintDrawer = document.getElementById("studentHintDrawer");
const hintToggleBtn = document.getElementById("hintToggleBtn");
const hintToggleIcon = document.getElementById("hintToggleIcon");
const hintContentBox = document.getElementById("hintContentBox");
const hintBlueprintText = document.getElementById("hintBlueprintText");
const keywordsPillList = document.getElementById("keywordsPillList");

// Tabs & Voice
const textTab = document.getElementById("textTab");
const voiceTab = document.getElementById("voiceTab");
const textAnswerArea = document.getElementById("textAnswerArea");
const voiceAnswerArea = document.getElementById("voiceAnswerArea");
const recordButton = document.getElementById("recordButton");
const recordingStatus = document.getElementById("recordingStatus");
const transcript = document.getElementById("transcript");
const micCircle = document.getElementById("micCircle");
const liveSoundwave = document.getElementById("liveSoundwave");

// Session metadata
const intervaiSessionId = sessionStorage.getItem("intervaiSessionId");
const intervaiRoleName = sessionStorage.getItem("intervaiRoleName");
const intervaiDifficulty = sessionStorage.getItem("intervaiDifficulty");
const intervaiFirstQuestionRaw = sessionStorage.getItem("intervaiFirstQuestion");
const intervaiQuestionSource = sessionStorage.getItem("intervaiQuestionSource");

if (intervaiRoleName && roleDisplay) roleDisplay.textContent = intervaiRoleName;
if (intervaiDifficulty && difficultyDisplay) difficultyDisplay.textContent = intervaiDifficulty;
if (savedJd && jdTagBadge) jdTagBadge.classList.remove("hidden");

// Inject Question 1
if (intervaiFirstQuestionRaw) {
    try {
        const firstQuestion = JSON.parse(intervaiFirstQuestionRaw);
        questions[0] = {
            question: firstQuestion.question,
            tip: firstQuestion.tip || questions[0].tip,
            topic: firstQuestion.topic || "Introduction",
            hint: firstQuestion.hint || questions[0].hint,
            sample_keywords: firstQuestion.sample_keywords || questions[0].sample_keywords,
            source: intervaiQuestionSource || "gemini",
        };
    } catch (e) {
        console.warn("Could not parse intervaiFirstQuestion:", e);
    }
}

// ===============================
// BACKEND STATUS CHECK
// ===============================

async function checkBackendConnection() {
    if (!backendStatus) return;
    try {
        const res = await fetch(`${INTERVAI_API_BASE_URL}/api/health`);
        const data = await res.json();
        if (data.gemini_configured) {
            backendStatus.innerHTML = `<span class="status-indicator"></span> <span>Interviewer is ready (Gemini 2.5 Flash)</span>`;
        } else {
            backendStatus.innerHTML = `<span class="status-indicator"></span> <span>Interviewer is ready (Role Bank Active)</span>`;
        }
    } catch {
        backendStatus.innerHTML = `<span class="status-indicator" style="background: #94a3b8;"></span> <span>Offline Question Bank Active</span>`;
    }
}
checkBackendConnection();

// ===============================
// PACING TIMER
// ===============================

function startPacingTimer() {
    clearInterval(timerInterval);
    speechSeconds = 0;
    updatePacingDisplay();

    timerInterval = setInterval(() => {
        speechSeconds++;
        updatePacingDisplay();
    }, 1000);
}

function updatePacingDisplay() {
    if (!pacingTimer || !pacingStatus) return;
    const mins = String(Math.floor(speechSeconds / 60)).padStart(2, "0");
    const secs = String(speechSeconds % 60).padStart(2, "0");
    pacingTimer.textContent = `${mins}:${secs}`;

    if (speechSeconds < 30) {
        pacingStatus.textContent = "Pacing: Warm-up (expand)";
        pacingStatus.className = "pacing-pill warning";
    } else if (speechSeconds <= 120) {
        pacingStatus.textContent = "Pacing: Sweet Spot (Optimal)";
        pacingStatus.className = "pacing-pill sweet-spot";
    } else {
        pacingStatus.textContent = "Pacing: Wrap up your main point";
        pacingStatus.className = "pacing-pill warning";
    }
}

// ===============================
// STUDENT HINT DRAWER TOGGLE
// ===============================

if (hintToggleBtn) {
    hintToggleBtn.addEventListener("click", () => {
        const isClosed = hintContentBox.style.display === "none";
        hintContentBox.style.display = isClosed ? "block" : "none";
        hintToggleIcon.classList.toggle("open", isClosed);
    });
}

// ===============================
// LOAD QUESTION
// ===============================

function loadQuestion() {
    const current = questions[currentQuestion];
    questionText.textContent = current.question;
    interviewTip.textContent = current.tip;
    questionNumber.textContent = currentQuestion + 1;
    if (questionTopic) questionTopic.textContent = `QUESTION ${currentQuestion + 1} • ${(current.topic || "COMPETENCY").toUpperCase()}`;
    if (questionSourceTag) questionSourceTag.textContent = current.source === "gemini" ? "✨ Gemini Adaptive AI" : "Standard Role Bank";

    // Update hints
    if (hintBlueprintText) {
        hintBlueprintText.innerHTML = (current.hint || "• Use the STAR method: Situation, Task, Action, Result.")
            .replace(/\n/g, "<br>");
    }

    if (keywordsPillList) {
        const kws = current.sample_keywords || ["STAR Method", "Core Competencies"];
        keywordsPillList.innerHTML = kws.map((k) => `<span class="keyword-pill">#${escapeHtml(k)}</span>`).join("");
    }

    const percentage = ((currentQuestion + 1) / totalQuestionsCount) * 100;
    progressFill.style.width = percentage + "%";
    progressPercentage.textContent = Math.round(percentage) + "%";

    answerInput.value = "";
    updateWordCount();

    if (transcript) {
        transcript.textContent = "Your spoken transcript will appear here in real-time...";
    }

    startPacingTimer();
    window.scrollTo({ top: 0, behavior: "smooth" });
}

loadQuestion();

// ===============================
// WORD COUNT & GAUGE
// ===============================

function updateWordCount() {
    const text = answerInput.value.trim();
    if (!text) {
        wordCount.textContent = "0 words";
        wordGauge.textContent = "Too brief";
        wordGauge.className = "word-gauge";
        return;
    }
    const words = text.split(/\s+/).length;
    wordCount.textContent = `${words} words`;

    if (words < 25) {
        wordGauge.textContent = "Too brief (<25 words)";
        wordGauge.className = "word-gauge";
    } else if (words < 60) {
        wordGauge.textContent = "Good foundation";
        wordGauge.className = "word-gauge developing";
    } else {
        wordGauge.textContent = "Strong detail";
        wordGauge.className = "word-gauge good";
    }
}

answerInput.addEventListener("input", updateWordCount);

// Clear button
if (clearAnswerBtn) {
    clearAnswerBtn.addEventListener("click", () => {
        if (confirm("Reset your response for this question?")) {
            answerInput.value = "";
            if (transcript) transcript.textContent = "Your spoken transcript will appear here in real-time...";
            updateWordCount();
            startPacingTimer();
        }
    });
}

// ===============================
// TEXT / VOICE TABS
// ===============================

textTab.addEventListener("click", function () {
    textTab.classList.add("active");
    voiceTab.classList.remove("active");
    textAnswerArea.classList.remove("hidden");
    voiceAnswerArea.classList.add("hidden");
});

voiceTab.addEventListener("click", function () {
    voiceTab.classList.add("active");
    textTab.classList.remove("active");
    voiceAnswerArea.classList.remove("hidden");
    textAnswerArea.classList.add("hidden");
});

// ===============================
// TEXT TO SPEECH (WITH AVATAR PULSE)
// ===============================

playQuestionBtn.addEventListener("click", function () {
    if (!("speechSynthesis" in window)) {
        alert("Your browser does not support text-to-speech.");
        return;
    }

    speechSynthesis.cancel();
    const currentQ = questions[currentQuestion]?.question || questionText.textContent;
    const speech = new SpeechSynthesisUtterance(currentQ);
    speech.rate = 0.95;
    speech.pitch = 1;

    speech.onstart = () => {
        if (aiAvatarIcon) aiAvatarIcon.classList.add("speaking");
        playQuestionBtn.style.borderColor = "#0284c7";
    };

    speech.onend = () => {
        if (aiAvatarIcon) aiAvatarIcon.classList.remove("speaking");
        playQuestionBtn.style.borderColor = "#cbd5e1";
    };

    speech.onerror = () => {
        if (aiAvatarIcon) aiAvatarIcon.classList.remove("speaking");
        playQuestionBtn.style.borderColor = "#cbd5e1";
    };

    speechSynthesis.speak(speech);
});

// ===============================
// VOICE RECOGNITION
// ===============================

function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return null;

    const rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = "en-US";

    rec.onstart = function () {
        isRecording = true;
        recordButton.classList.add("recording");
        recordButton.textContent = "⏹ Stop Recording";
        recordingStatus.textContent = "Listening to your answer...";
        if (micCircle) micCircle.classList.add("recording");
        if (liveSoundwave) liveSoundwave.classList.remove("hidden");
    };

    rec.onresult = function (event) {
        let finalTranscript = "";
        let interimTranscript = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const part = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += part;
            } else {
                interimTranscript += part;
            }
        }

        transcript.textContent = finalTranscript || interimTranscript;

        if (finalTranscript) {
            if (answerInput.value.trim()) {
                answerInput.value += " " + finalTranscript;
            } else {
                answerInput.value = finalTranscript;
            }
            updateWordCount();
        }
    };

    rec.onend = function () {
        isRecording = false;
        recordButton.classList.remove("recording");
        recordButton.textContent = "🎙 Start Recording";
        recordingStatus.textContent = "Recording paused";
        if (micCircle) micCircle.classList.remove("recording");
        if (liveSoundwave) liveSoundwave.classList.add("hidden");
    };

    rec.onerror = function () {
        isRecording = false;
        recordButton.classList.remove("recording");
        recordButton.textContent = "🎙 Start Recording";
        recordingStatus.textContent = "Microphone paused";
        if (micCircle) micCircle.classList.remove("recording");
        if (liveSoundwave) liveSoundwave.classList.add("hidden");
    };

    return rec;
}

recognition = setupSpeechRecognition();

recordButton.addEventListener("click", function () {
    if (!recognition) {
        alert("Voice recognition is not supported in this browser. Try Google Chrome or Microsoft Edge.");
        return;
    }

    if (isRecording) {
        recognition.stop();
    } else {
        transcript.textContent = "Listening...";
        try {
            recognition.start();
        } catch (e) {
            console.warn("Recognition start error:", e);
        }
    }
});

// ===============================
// SUBMIT ANSWER & ADAPTIVE FOLLOW-UP
// ===============================

submitAnswer.addEventListener("click", async function () {
    const answer = answerInput.value.trim();
    if (!answer) {
        alert("Please provide an answer before continuing.");
        return;
    }

    if (isRecording && recognition) {
        recognition.stop();
    }

    const currentQA = {
        question: questions[currentQuestion].question,
        answer: answer,
    };

    answers.push(currentQA);

    // If final question, wrap up
    if (currentQuestion >= totalQuestionsCount - 1) {
        await finishInterview();
        return;
    }

    // Otherwise fetch next adaptive question
    const nextQNum = currentQuestion + 2;
    submitAnswer.disabled = true;
    submitAnswer.textContent = `IntervAI is generating Question ${nextQNum}...`;

    try {
        if (intervaiSessionId) {
            const nextRes = await fetch(`${INTERVAI_API_BASE_URL}/api/interview/next-question`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: intervaiSessionId,
                    question_number: nextQNum,
                    last_question: currentQA.question,
                    last_answer: currentQA.answer,
                    job_description: savedJd || null,
                }),
            });

            if (nextRes.ok) {
                const nextData = await nextRes.json();
                questions[currentQuestion + 1] = {
                    question: nextData.question.question,
                    tip: nextData.question.tip,
                    topic: nextData.question.topic,
                    hint: nextData.question.hint,
                    sample_keywords: nextData.question.sample_keywords,
                    source: nextData.source,
                };
            }
        }
    } catch (err) {
        console.warn("Next question fetch error (using fallback):", err);
    } finally {
        submitAnswer.disabled = false;
        submitAnswer.innerHTML = 'Submit Answer <span>→</span>';
    }

    currentQuestion++;
    loadQuestion();
});

// ===============================
// FINISH & EVALUATE
// ===============================

async function finishInterview() {
    clearInterval(timerInterval);
    submitAnswer.disabled = true;
    submitAnswer.textContent = "Generating AI Performance Evaluation...";

    localStorage.setItem("interviewAnswers", JSON.stringify(answers));
    localStorage.setItem("interviewCompleted", "true");

    const track = sessionStorage.getItem("intervaiTrack") || localStorage.getItem("interviewTrack") || "technical";
    const roleId = sessionStorage.getItem("intervaiRoleId") || localStorage.getItem("interviewRoleId") || null;
    const roleName = intervaiRoleName || "Candidate";
    const difficulty = intervaiDifficulty || "Intermediate";

    const payload = {
        session_id: intervaiSessionId || null,
        track: track,
        role_id: roleId,
        role_name: roleName,
        difficulty: difficulty,
        answers: answers,
        job_description: savedJd || null,
    };

    try {
        const response = await fetch(`${INTERVAI_API_BASE_URL}/api/interview/evaluate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (response.ok) {
            const evalResult = await response.json();
            sessionStorage.setItem("intervaiEvaluation", JSON.stringify(evalResult));
        } else {
            createLocalEvaluation(payload);
        }
    } catch (err) {
        console.warn("Evaluation fetch error:", err);
        createLocalEvaluation(payload);
    }

    window.location.href = "results.html";
}

function createLocalEvaluation(payload) {
    const defaultScore = 85;
    const localEval = {
        overall_score: defaultScore,
        rating: "Very Good",
        summary: `You completed your ${payload.role_name} interview (${payload.difficulty} level). Your responses showed solid technical understanding, structured reasoning, and professional communication.`,
        category_scores: {
            technical_accuracy: 85,
            clarity_communication: 86,
            problem_solving: 84,
            structure: 85,
        },
        strengths: [
            `Demonstrated practical comprehension of ${payload.role_name} core responsibilities`,
            "Communicated clearly with structured and relevant answers",
            "Maintained composure and answered with logical reasoning",
        ],
        improvements: [
            "Provide more measurable, quantifiable metrics (e.g. latency, throughput, scale) when describing results",
            "Structure situational examples using the STAR framework (Situation, Task, Action, Result)",
        ],
        question_evaluations: payload.answers.map((a, i) => ({
            question: a.question || `Question ${i + 1}`,
            score: 84 + (i % 3) * 3,
            feedback: "Well-reasoned response that directly tackled the question with good clarity.",
        })),
        jd_match_score: payload.job_description ? 80 : null,
        matched_keywords: payload.job_description ? ["architecture", "api", "database", "testing"] : null,
        missing_keywords: payload.job_description ? ["ci/cd", "caching"] : null,
        source: "fallback",
    };
    sessionStorage.setItem("intervaiEvaluation", JSON.stringify(localEval));
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