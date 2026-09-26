"""
Fallback interview questions bank for IntervAI.

Provides complete 5-question sequential interviews tailored to each role
with student-friendly STAR hints and recommended keywords.
"""

from typing import Any

ROLE_FALLBACK_QUESTIONS: dict[str, list[dict[str, Any]]] = {
    "hr_behavioral": [
        {
            "question": "To start, could you walk me through your background and what motivates your interest in this role?",
            "topic": "Introduction",
            "question_type": "behavioral",
            "tip": "Keep it concise (1-2 minutes): highlight your education, core strengths, and alignment with our mission.",
            "hint": "• Present: Your current education / technical focus\n• Past: 1-2 major projects or milestones that shaped your passion\n• Future: Why this specific role and company excite you",
            "sample_keywords": ["passionate", "milestone", "collaboration", "growth mindset"]
        },
        {
            "question": "Describe a project or situation where you had to collaborate closely with a team under a tight deadline.",
            "topic": "Teamwork",
            "question_type": "behavioral",
            "tip": "Use the STAR method: Situation, Task, Action, and Result. Emphasize constructive communication.",
            "hint": "• Situation: The project context and tight deadline\n• Task: Your specific responsibility\n• Action: How you coordinated, divided tasks, or resolved blockers\n• Result: Delivered on time, learned effective delegation",
            "sample_keywords": ["STAR method", "clear communication", "prioritization", "successful delivery"]
        },
        {
            "question": "Tell me about a time you experienced a disagreement or conflict with a teammate or stakeholder. How did you resolve it?",
            "topic": "Conflict Resolution",
            "question_type": "behavioral",
            "tip": "Show emotional intelligence, active listening, and how you found common ground focused on project goals.",
            "hint": "• Situation: Different opinions on technical approach or task ownership\n• Action: Scheduled a 1-on-1, actively listened, focused on data/objective criteria\n• Result: Reached a consensus and maintained a positive working relationship",
            "sample_keywords": ["active listening", "compromise", "data-driven", "mutual respect"]
        },
        {
            "question": "Can you describe a situation where a plan or project didn't go as expected? What did you learn from that experience?",
            "topic": "Adaptability & Resilience",
            "question_type": "behavioral",
            "tip": "Own the setback objectively. Focus on the lessons learned and how you changed your approach afterward.",
            "hint": "• Situation: A bug, delayed deliverable, or scope change\n• Action: Took accountability, communicated early, implemented a workaround\n• Result & Learning: What preventative measure you adopted for future work",
            "sample_keywords": ["accountability", "pivot", "root cause", "continuous improvement"]
        },
        {
            "question": "Where do you see yourself professionally in the next 2 to 3 years, and how will this role help you get there?",
            "topic": "Career Goals",
            "question_type": "behavioral",
            "tip": "Show ambition paired with realistic growth milestones that demonstrate commitment to the team.",
            "hint": "• Skill Growth: Mastering production best practices and system architecture\n• Value Added: Taking ownership of features and mentoring juniors\n• Alignment: Growing into a reliable core contributor in the organization",
            "sample_keywords": ["technical mastery", "mentorship", "ownership", "long-term commitment"]
        },
    ],
    "full_stack_developer": [
        {
            "question": "Tell me about your background and walk me through a major full-stack application you've designed and built.",
            "topic": "Architecture & Projects",
            "question_type": "project-based",
            "tip": "Mention your tech stack choices for both frontend and backend, and the core user problem you solved.",
            "hint": "• Problem: What user problem did your app solve?\n• Architecture: Frontend (React/Vue), Backend (FastAPI/Node), Database (PostgreSQL/MongoDB)\n• Highlight: One technical challenge you overcame (e.g. auth, state flow, caching)",
            "sample_keywords": ["REST API", "State Management", "Database Design", "Authentication"]
        },
        {
            "question": "How do you design a clean, maintainable RESTful API? What principles do you follow for status codes, error handling, and versioning?",
            "topic": "API Design",
            "question_type": "conceptual",
            "tip": "Discuss consistent payload structures, HTTP verbs, idempotent methods, and centralized error middleware.",
            "hint": "• Verbs & Nouns: GET /items, POST /items, PUT/PATCH, DELETE\n• Status Codes: 200/201 (success), 400 (bad request), 401/403 (auth), 404, 500\n• Best Practices: Centralized exception handlers, versioning (/api/v1), consistent JSON format",
            "sample_keywords": ["Idempotency", "HTTP Status Codes", "JSON Schema", "Middleware"]
        },
        {
            "question": "How do you handle state management, asynchronous operations, and responsiveness on the frontend when handling large datasets?",
            "topic": "Frontend Performance",
            "question_type": "architecture",
            "tip": "Mention component modularity, pagination/virtualization, caching, and clean client-side state flow.",
            "hint": "• State Flow: Local state (useState) vs global store (Context / Redux)\n• Large Data: Virtual scrolling / pagination to prevent DOM bloat\n• UX: Skeleton loaders, optimistic UI updates, debouncing search inputs",
            "sample_keywords": ["Virtual DOM", "Debouncing", "Pagination", "Optimistic Updates"]
        },
        {
            "question": "Describe how you approach database schema design, indexing, and preventing common performance bottlenecks like N+1 queries.",
            "topic": "Database Optimization",
            "question_type": "debugging",
            "tip": "Explain indexing strategies, query execution plans, normalization vs denormalization, and ORM optimizations.",
            "hint": "• Schema: Normalization up to 3NF, foreign keys and constraints\n• Indexing: B-tree indexes on foreign keys and frequently queried fields (WHERE/JOIN)\n• N+1 Fix: Using eager loading (JOINs / select_related) instead of lazy querying in a loop",
            "sample_keywords": ["B-Tree Indexing", "Eager Loading", "Foreign Keys", "Execution Plan (EXPLAIN)"]
        },
        {
            "question": "How do you address security (e.g., auth, CORS, input validation, SQL injection) and deploy your full-stack applications to production?",
            "topic": "Security & Deployment",
            "question_type": "trade-off",
            "tip": "Highlight JWT/session security, HTTPS, sanitization libraries, Docker containerization, and CI/CD pipelines.",
            "hint": "• Security: Parameterized queries (ORM), input validation with Pydantic/Zod, secure HTTP-only cookies, CORS whitelist\n• Deployment: Docker container, cloud hosting (Render/AWS/Vercel), automated CI/CD pipeline",
            "sample_keywords": ["JWT / Cookies", "Docker Container", "CORS Configuration", "CI/CD Pipeline"]
        },
    ],
    "ml_engineer": [
        {
            "question": "Tell me about your background in machine learning and a specific model or ML pipeline you recently developed.",
            "topic": "Introduction & ML Projects",
            "question_type": "project-based",
            "tip": "Clearly describe the dataset, the business or research problem, your modeling strategy, and final results.",
            "hint": "• Objective: What were you predicting or classifying?\n• Pipeline: Data cleaning -> Feature extraction -> Baseline model -> Tuned model\n• Result: Metrics achieved (F1, Accuracy, AUC) and real-world significance",
            "sample_keywords": ["Pipeline", "Feature Engineering", "Baseline Model", "Evaluation Metrics"]
        },
        {
            "question": "How do you approach exploratory data analysis, data cleaning, and handling challenges like missing values or severe class imbalance?",
            "topic": "Data Preprocessing",
            "question_type": "scenario",
            "tip": "Mention techniques like SMOTE, class-weighted loss, stratified sampling, and imputation trade-offs.",
            "hint": "• Missing Data: Imputation (median/KNN) vs dropping based on missingness mechanism\n• Imbalance: SMOTE (oversampling), random undersampling, or class_weight='balanced'\n• Validation: Always use Stratified K-Fold to maintain class proportions",
            "sample_keywords": ["SMOTE", "Class Weights", "Stratified K-Fold", "Data Imputation"]
        },
        {
            "question": "Walk me through how you choose between different model architectures and diagnose high bias (underfitting) versus high variance (overfitting).",
            "topic": "Model Selection & Generalization",
            "question_type": "conceptual",
            "tip": "Discuss learning curves, regularization (L1/L2, dropout), cross-validation, and complexity trade-offs.",
            "hint": "• High Bias: Poor train and validation performance -> Increase model complexity, add features\n• High Variance: High train accuracy, low validation accuracy -> Add L1/L2 regularization, dropout, more data\n• Trade-off: Start with simple linear/tree baseline before deep learning",
            "sample_keywords": ["Bias-Variance Tradeoff", "L1/L2 Regularization", "Dropout", "Learning Curves"]
        },
        {
            "question": "Which evaluation metrics do you prioritize (e.g., Precision, Recall, F1, ROC-AUC) when accuracy is misleading, and how do you validate your choices?",
            "topic": "Evaluation Metrics",
            "question_type": "trade-off",
            "tip": "Tie your metric choice directly to the business cost of false positives versus false negatives.",
            "hint": "• High Cost of False Negatives (e.g. medical diagnosis, fraud): Prioritize Recall\n• High Cost of False Positives (e.g. spam filter, loan denial): Prioritize Precision\n• Overall: F1-score harmonic mean or ROC-AUC for threshold-independent evaluation",
            "sample_keywords": ["Precision vs Recall", "F1 Score", "Confusion Matrix", "ROC-AUC"]
        },
        {
            "question": "How do you deploy and monitor ML models in production to detect data drift, concept drift, or latency degradation over time?",
            "topic": "MLOps & Deployment",
            "question_type": "architecture",
            "tip": "Mention serving frameworks (FastAPI/TorchServe), containerization, monitoring drift, and CI/CD for models.",
            "hint": "• Serving: Wrap model in a FastAPI microservice with ONNX/TensorRT for fast inference\n• Drift: Monitor input feature distributions (KS test) and ground truth performance degradation\n• Pipeline: CI/CD with automated retraining triggers and fallback models",
            "sample_keywords": ["Data Drift", "Model Serving (FastAPI)", "Latency Optimization", "Model Monitoring"]
        },
    ],
    "data_analyst": [
        {
            "question": "Tell me about your background and a data analysis project where your findings directly influenced a business or product decision.",
            "topic": "Introduction & Impact",
            "question_type": "project-based",
            "tip": "Highlight the business context, the question you set out to answer, and the measurable impact of your recommendation.",
            "hint": "• Context: What business question or drop in metric was investigated?\n• Method: SQL extraction -> Pandas cleaning -> Cohort/trend analysis -> Visual dashboard\n• Impact: Recommended change that drove X% increase in retention/revenue",
            "sample_keywords": ["Business KPI", "Actionable Insight", "Cohort Analysis", "Data Storytelling"]
        },
        {
            "question": "What is your approach to writing complex SQL queries? How do you leverage window functions, CTEs, and self-joins for cohort or trend analysis?",
            "topic": "SQL & Querying",
            "question_type": "conceptual",
            "tip": "Discuss readability, execution efficiency, window partitions, and optimizing aggregation pipelines.",
            "hint": "• CTEs: Break complex multi-stage aggregations into clean WITH clauses\n• Window Functions: ROW_NUMBER(), RANK(), LAG()/LEAD() OVER (PARTITION BY ... ORDER BY ...)\n• Optimization: Filter early with WHERE, index join columns, avoid unnecessary SELECT *",
            "sample_keywords": ["Window Functions (PARTITION BY)", "Common Table Expressions (CTEs)", "LEAD / LAG", "Query Optimization"]
        },
        {
            "question": "How do you handle dirty, inconsistent, or missing data when working on an analysis? Can you share a time you discovered an anomaly in raw data?",
            "topic": "Data Quality & Cleaning",
            "question_type": "debugging",
            "tip": "Explain your validation steps, anomaly detection methods, and how you documented assumptions transparently.",
            "hint": "• Detection: Summary stats (describe()), box plots, checking NULL rates, finding duplicate primary keys\n• Resolution: Documenting cleaning rules, deduplicating, validating with domain experts\n• Communication: Transparently flagging limitations in reports",
            "sample_keywords": ["Data Validation", "Outlier Detection", "Null Imputation", "Data Lineage"]
        },
        {
            "question": "When presenting technical findings and complex data to non-technical stakeholders, how do you decide what visualizations and key metrics to present?",
            "topic": "Stakeholder Communication",
            "question_type": "scenario",
            "tip": "Emphasize storytelling with data, avoiding clutter, choosing the right chart types, and focusing on actionable takeaways.",
            "hint": "• Audience: Lead with bottom-line takeaway (revenue, conversion, churn)\n• Chart Choice: Line for trends, bar for categories, avoid cluttered pie charts\n• Delivery: Highlight 'So What?' and next recommended steps",
            "sample_keywords": ["Data Storytelling", "Executive Summary", "Actionable Recommendations", "Dashboarding"]
        },
        {
            "question": "How do you design and interpret A/B tests or experiment results to ensure statistical significance before recommending a rollout?",
            "topic": "Experimentation & Statistics",
            "question_type": "trade-off",
            "tip": "Mention sample size calculation, p-values, confidence intervals, and avoiding common pitfalls like peeking at data early.",
            "hint": "• Setup: Define primary KPI, null hypothesis, calculate minimum sample size (power analysis)\n• Analysis: Compare Control vs Treatment with two-sample t-test / Z-test, check p-value < 0.05\n• Safeguard: Check for sample ratio mismatch (SRM) and avoid early stopping",
            "sample_keywords": ["Hypothesis Testing", "p-value & Confidence Interval", "Sample Size Power", "Statistical Significance"]
        },
    ],
    "python_developer": [
        {
            "question": "Tell me about your experience with Python and walk me through a complex application or tool you've built using the language.",
            "topic": "Python Architecture",
            "question_type": "project-based",
            "tip": "Highlight the problem, libraries used, architectural design, and why Python was well-suited for it.",
            "hint": "• Project Scope: Backend service, scraper, CLI tool, or data pipeline\n• Design: Modular packages, typing (type hints), clean exception hierarchy\n• Highlight: One performance or concurrency optimization",
            "sample_keywords": ["Type Hinting", "Modular Architecture", "Virtual Environments", "Clean Code"]
        },
        {
            "question": "How does Python handle memory management and garbage collection? Can you explain the role of reference counting and the cyclic GC?",
            "topic": "Python Internals",
            "question_type": "conceptual",
            "tip": "Mention reference counting, generational garbage collection, cyclic references, and weak references.",
            "hint": "• Reference Counting: Primary mechanism (increments when referenced, deallocates at 0)\n• Cyclic GC: Detects circular references using 3 generational heaps (Gen 0, 1, 2)\n• Tooling: Using weakref or gc module for inspecting memory leaks",
            "sample_keywords": ["Reference Counting", "Generational GC", "Circular References", "Memory Profiling"]
        },
        {
            "question": "Explain the Global Interpreter Lock (GIL) and how you approach concurrency in Python using threading, multiprocessing, and asyncio.",
            "topic": "Concurrency & GIL",
            "question_type": "trade-off",
            "tip": "Contrast I/O-bound tasks (asyncio/threading) with CPU-bound tasks (multiprocessing) and their trade-offs.",
            "hint": "• GIL: Mutex that prevents multiple native threads from executing Python bytecode simultaneously\n• I/O-bound: Use asyncio or threading (GIL is released during network/disk I/O)\n• CPU-bound: Use multiprocessing (spawns separate processes with independent Python interpreters)",
            "sample_keywords": ["GIL (Global Interpreter Lock)", "asyncio / Event Loop", "multiprocessing", "I/O vs CPU bound"]
        },
        {
            "question": "How do you structure Python code for maintainability using object-oriented principles, generators, decorators, and context managers?",
            "topic": "Pythonic Design Patterns",
            "question_type": "conceptual",
            "tip": "Give a practical example of a custom decorator or context manager and why it reduces boilerplate.",
            "hint": "• Decorators: @functools.wraps for logging, authentication, or timing execution\n• Context Managers: with statement (__enter__ and __exit__) for reliable resource cleanup\n• Generators: yield statement for streaming large datasets in constant memory",
            "sample_keywords": ["Decorators", "Context Managers", "Generators (yield)", "Magic Methods"]
        },
        {
            "question": "What is your approach to testing and profiling Python applications? How do you detect and fix memory leaks or CPU bottlenecks?",
            "topic": "Testing & Optimization",
            "question_type": "debugging",
            "tip": "Mention pytest, mock fixtures, cProfile, tracemalloc, and optimizing algorithmic complexity.",
            "hint": "• Testing: pytest with fixtures, parametrized tests, unittest.mock for external APIs\n• Profiling: cProfile for CPU bottlenecks, tracemalloc for memory allocations\n• Optimization: Using built-in collections, vectorization (NumPy), or list comprehensions",
            "sample_keywords": ["pytest & Fixtures", "cProfile", "Mocking APIs", "tracemalloc"]
        },
    ],
    "java_developer": [
        {
            "question": "Tell me about your Java background and describe a key enterprise or backend project you have worked on.",
            "topic": "Java Projects",
            "question_type": "project-based",
            "tip": "Highlight the Java version, frameworks used (e.g. Spring Boot), architecture, and your specific responsibilities.",
            "hint": "• Stack: Java 17/21, Spring Boot, Maven/Gradle, Hibernate/JPA, PostgreSQL\n• Architecture: Controller -> Service -> Repository layer pattern\n• Achievement: Implemented secure REST endpoints and optimized query latency",
            "sample_keywords": ["Spring Boot", "Layered Architecture", "Maven / Gradle", "JPA / Hibernate"]
        },
        {
            "question": "Can you explain the core differences between an interface and an abstract class in modern Java, and when you would prefer one over the other?",
            "topic": "OOP Principles",
            "question_type": "conceptual",
            "tip": "Mention default/static methods in interfaces, multiple inheritance of type, and is-a vs can-do relationships.",
            "hint": "• Abstract Class: Can hold state (instance variables), constructors; used for 'is-a' relationships and shared implementation\n• Interface: Defines a contract / 'can-do' behavior; a class can implement multiple interfaces; supports default/static methods since Java 8",
            "sample_keywords": ["Contract vs State", "Multiple Inheritance", "Default Methods", "Polymorphism"]
        },
        {
            "question": "How do you handle multithreading and thread safety in Java? Explain concepts like the volatile keyword, synchronized blocks, and java.util.concurrent.",
            "topic": "Concurrency & Thread Safety",
            "question_type": "conceptual",
            "tip": "Discuss atomic variables, thread pools (ExecutorService), concurrent collections, and the Java Memory Model.",
            "hint": "• volatile: Ensures visibility across threads by reading directly from main memory\n• synchronized: Mutual exclusion (mutex) on monitor lock for critical sections\n• java.util.concurrent: ExecutorService thread pools, ConcurrentHashMap, AtomicInteger",
            "sample_keywords": ["volatile", "ExecutorService", "ConcurrentHashMap", "Atomic Variables"]
        },
        {
            "question": "How does the Spring Framework (or Spring Boot) handle Dependency Injection, Inversion of Control, and Bean lifecycle management?",
            "topic": "Spring Framework",
            "question_type": "architecture",
            "tip": "Explain the Spring ApplicationContext, autowiring, singleton vs prototype scope, and common annotations.",
            "hint": "• IoC: Framework creates and manages object lifecycles rather than manual new operators\n• DI: Constructor injection (recommended) vs @Autowired field injection\n• Scopes: Singleton (default, one per container) vs Prototype (new per request)",
            "sample_keywords": ["Inversion of Control (IoC)", "Constructor Injection", "Bean Scopes", "ApplicationContext"]
        },
        {
            "question": "How does the Java Virtual Machine (JVM) manage memory (Heap, Stack, Metaspace), and how do you troubleshoot an OutOfMemoryError?",
            "topic": "JVM & Performance",
            "question_type": "debugging",
            "tip": "Discuss JVM memory regions, garbage collection algorithms (G1, ZGC), heap dumps, and profilers.",
            "hint": "• Memory: Stack (thread-specific method frames & local primitives) vs Heap (objects & garbage collected)\n• Troubleshooting: Take heap dump on OOM (-XX:+HeapDumpOnOutOfMemoryError), analyze in Eclipse Memory Analyzer (MAT) or VisualVM\n• Tuning: Garbage collectors like G1GC or ZGC for low-pause performance",
            "sample_keywords": ["Heap vs Stack", "G1 Garbage Collector", "Heap Dump Analysis", "OutOfMemoryError"]
        },
    ],
}


def get_fallback_opening_question(track: str, role_id: str | None) -> dict:
    """Returns the opening question for the chosen track and role."""
    key = "hr_behavioral" if track == "hr_behavioral" else (role_id or "full_stack_developer")
    questions = ROLE_FALLBACK_QUESTIONS.get(key, ROLE_FALLBACK_QUESTIONS["hr_behavioral"])
    return questions[0]


def get_fallback_question(track: str, role_id: str | None, question_number: int) -> dict:
    """
    Returns the fallback question at the given 1-based index for the track/role.
    Cycles safely if question_number exceeds the bank length.
    """
    key = "hr_behavioral" if track == "hr_behavioral" else (role_id or "full_stack_developer")
    questions = ROLE_FALLBACK_QUESTIONS.get(key, ROLE_FALLBACK_QUESTIONS["hr_behavioral"])
    idx = max(0, min(question_number - 1, len(questions) - 1))
    return questions[idx]
