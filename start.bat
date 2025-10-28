@echo off
echo ==========================================
echo   Agno AI Service - Quick Start
echo ==========================================

REM Check if .env exists
if not exist .env (
    echo Warning: No .env file found
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env and add your OPENAI_KEY
    echo    notepad .env
    echo.
    pause
)

REM Check if venv exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ==========================================
echo   Starting Agno AI Service
echo ==========================================
echo.

REM Run the service
python main.py

pause
