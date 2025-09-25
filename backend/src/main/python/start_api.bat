@echo off
REM Startup script for Python Portfolio Optimization API (Windows)
REM This script starts the FastAPI server for portfolio optimization

echo Starting Python Portfolio Optimization API...

REM Navigate to the Python source directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "..\..\..\venv" (
    if not exist "..\..\..\.venv" (
        echo Virtual environment not found. Please create one first:
        echo python -m venv .venv
        echo .venv\Scripts\activate
        echo pip install -r requirements.txt
        pause
        exit /b 1
    )
)

REM Activate virtual environment
if exist "..\..\..\.venv\Scripts\activate.bat" (
    call "..\..\..\.venv\Scripts\activate.bat"
) else if exist "..\..\..\venv\Scripts\activate.bat" (
    call "..\..\..\venv\Scripts\activate.bat"
) else (
    echo Could not find virtual environment activation script
    pause
    exit /b 1
)

REM Install/upgrade dependencies
echo Installing/updating Python dependencies...
pip install -r requirements.txt

REM Start the FastAPI server
echo Starting FastAPI server on http://localhost:8001...
uvicorn portfolio_api:app --host 0.0.0.0 --port 8001 --reload --log-level info

echo Python Portfolio Optimization API stopped.
pause