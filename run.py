"""
IntervAI - One-Click Application Runner.

Starts the full-stack IntervAI application on http://localhost:8000
and automatically opens it in your default web browser.
"""

import os
import sys
import time
import webbrowser
from pathlib import Path

# Add project root and backend directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    import uvicorn
    from fastapi import FastAPI
    import pypdf
    import multipart
except ImportError:
    print("\n[!] Installing required packages...")
    import subprocess
    req_file = BACKEND_DIR / "requirements.txt"
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_file)])

from backend.config import settings
from backend.main import app


def open_browser():
    time.sleep(1.2)
    url = "http://localhost:8000"
    print(f"\n[*] Opening IntervAI in your web browser: {url}")
    webbrowser.open(url)


def main():
    print("=" * 65)
    print("           IntervAI — Adaptive AI Interview Simulator")
    print("=" * 65)
    print(f"[*] Root Directory : {ROOT_DIR}")
    print(f"[*] Port           : 8000")
    if settings.gemini_configured:
        print(f"[*] Gemini AI      : ENABLED ({settings.GEMINI_MODEL})")
    else:
        print(f"[*] Gemini AI      : STANDARD MODE (Add key in web UI or .env for live AI)")
    print(f"[*] Application URL: http://localhost:8000")
    print("=" * 65)

    # Launch browser in a background thread
    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Run the unified FastAPI server
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
