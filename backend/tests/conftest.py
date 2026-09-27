"""
Pytest configuration and shared fixtures for the IntervAI test suite.
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend directory and project root are in sys.path
TEST_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TEST_DIR.parent
ROOT_DIR = BACKEND_DIR.parent

for path in (str(BACKEND_DIR), str(ROOT_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

from backend.main import app
from backend.services import session_store


@pytest.fixture(autouse=True)
def clean_sessions():
    """Wipes in-memory session store between tests to ensure test isolation."""
    session_store._sessions.clear()
    yield
    session_store._sessions.clear()


@pytest.fixture
def client():
    """Provides a synchronous FastAPI TestClient instance."""
    return TestClient(app)
