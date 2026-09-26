@echo off
title IntervAI — AI Interview Simulator
cd /d "%~dp0"
echo ===================================================
echo     Starting IntervAI Server and Web Interface...
echo ===================================================

if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" run.py
) else if exist "..\venv\Scripts\python.exe" (
    "..\venv\Scripts\python.exe" run.py
) else (
    python run.py
)

pause
