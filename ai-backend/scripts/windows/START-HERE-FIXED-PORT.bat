@echo off
setlocal

echo ===============================================
echo AI Backend Launcher (Fixed Port - Backup)
echo ===============================================
echo.

REM Store paths
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..\") do set "UNC_PROJECT_PATH=%%~fI"
echo Script location: %SCRIPT_DIR%
echo Project root: %UNC_PROJECT_PATH%

REM ---- Config ----
set "API_PORT=5050"
set "VLLM_PORT=8000"
set "MODEL_ID=TinyLlama/TinyLlama-1.1B-Chat-v1.0"
set "WSL_DISTRO="
set "WSL_PROJECT_PATH=/Projects/Doma Backend/Program/ai-backend"
set "GW_VENV=%USERPROFILE%\ai-backend-gateway-venv"
set "DB_DIR=%USERPROFILE%\ai-backend-data"
set "DATABASE_URL=sqlite:///%DB_DIR%/ai_backend.db"

echo.
echo [preflight] Checking tools...

REM Check WSL
where wsl.exe >nul 2>nul || (
    echo [error] WSL not found. Install WSL first.
    goto :fail_pause
)

REM Check Python
where py.exe >nul 2>nul || (
    echo [warning] Python launcher not found, trying python...
    set "PY_LAUNCH=python"
)
if not defined PY_LAUNCH set "PY_LAUNCH=py -3"

REM Check project files
echo [preflight] Checking project files at: %UNC_PROJECT_PATH%
if not exist "%UNC_PROJECT_PATH%\requirements.txt" (
    echo [error] requirements.txt not found at: %UNC_PROJECT_PATH%
    goto :fail_pause
)

echo [ok] All checks passed!

REM WSL command setup
set "WSL_LABEL=default WSL distro"
if not "%WSL_DISTRO%"=="" set "WSL_LABEL=%WSL_DISTRO%"
set "WSL_CMD=wsl.exe"
if not "%WSL_DISTRO%"=="" set "WSL_CMD=wsl.exe -d %WSL_DISTRO%"

echo.
echo [1/2] Starting vLLM in WSL (%WSL_LABEL%) on port %VLLM_PORT%...

REM Launch vLLM in WSL
start "AI Server (WSL vLLM)" %WSL_CMD% -- bash -lc "echo 'Starting vLLM setup...'; export DEBIAN_FRONTEND=noninteractive; echo 'Installing system packages...'; sudo apt-get update -y && sudo apt-get install -y python3 python3-venv python3-pip; echo 'Changing to project directory...'; cd '%WSL_PROJECT_PATH%' || { echo 'ERROR: Cannot cd to %WSL_PROJECT_PATH%'; read -p 'Press Enter to close...'; exit 1; }; echo 'Setting up Python virtual environment...'; if [ ! -d .vllm-venv ]; then python3 -m venv .vllm-venv; fi; source .vllm-venv/bin/activate; echo 'Installing Python packages...'; python -m pip install --upgrade pip; python -m pip install vllm; echo 'Starting vLLM server...'; python -m vllm.entrypoints.openai.api_server --model '%MODEL_ID%' --host 0.0.0.0 --port %VLLM_PORT% --served-model-name '%MODEL_ID%' || { echo 'vLLM failed to start. Check the model name or internet connection.'; read -p 'Press Enter to close...'; }"

echo.
echo [2/2] Starting Gateway on Windows (port %API_PORT%)...

REM Launch Gateway in PowerShell with execution policy bypass
set "VLLM_BASE_URL=http://localhost:%VLLM_PORT%/v1"
if not exist "%DB_DIR%" mkdir "%DB_DIR%"
start "Gateway (Windows)" powershell -ExecutionPolicy Bypass -NoExit -Command "$ErrorActionPreference='Stop'; $env:API_PORT='%API_PORT%'; $env:VLLM_BASE_URL='%VLLM_BASE_URL%'; $env:DATABASE_URL='%DATABASE_URL%'; if (!(Test-Path '%GW_VENV%\Scripts\Activate.ps1')) { %PY_LAUNCH% -m venv '%GW_VENV%' }; & '%GW_VENV%\Scripts\Activate.ps1'; Set-Location '%UNC_PROJECT_PATH%'; pip install --upgrade pip; pip install -r 'requirements.txt'; $env:PYTHONPATH=(Get-Location).Path + '\'; uvicorn app.main:app --host 0.0.0.0 --port $env:API_PORT"

echo.
echo ===============================================
echo SUCCESS! Launched both servers:
echo - vLLM (WSL): http://localhost:%VLLM_PORT%/v1
echo - Gateway (Windows): http://localhost:%API_PORT%
echo.
echo Test URLs:
echo - Health: http://localhost:%API_PORT%/health
echo - Models: http://localhost:%API_PORT%/api/models
echo ===============================================
echo.
echo This window will stay open so you can see any messages.
echo Press any key to close...
pause >nul
goto :end

:fail_pause
echo.
echo Launch failed. Press any key to close...
pause >nul

:end
endlocal
