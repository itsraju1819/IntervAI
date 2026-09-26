// ========================================
// IntervAI - Frontend API configuration
// ========================================
//
// Single source of truth for the backend base URL.
// When running via HTTP/HTTPS (e.g. localhost:8000 or production domain),
// it automatically points to the current server origin.
// When opened directly via file://, it defaults to http://localhost:8000.

const INTERVAI_API_BASE_URL = (
    window.location.protocol.startsWith("http")
) ? window.location.origin : "http://localhost:8000";
