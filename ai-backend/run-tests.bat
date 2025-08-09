@echo off
echo ===============================================
echo AI Backend Test Runner
echo ===============================================
echo.
echo This will test all endpoints on your AI backend.
echo Make sure both servers are running first!
echo.
echo [Checking Python...]

REM Check if Python is available
python --version >nul 2>nul
if errorlevel 1 (
    py --version >nul 2>nul
    if errorlevel 1 (
        echo ERROR: Python not found. Install Python first.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

echo Python found: %PYTHON_CMD%
echo.
echo [Installing required packages...]
%PYTHON_CMD% -m pip install requests >nul 2>nul

echo.
echo [Running tests...]
echo.
%PYTHON_CMD% "%~dp0test-endpoints.py"

echo.
echo ===============================================
echo Tests completed!
echo ===============================================
pause
