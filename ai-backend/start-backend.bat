@echo off
setlocal

REM ---- Config (edit these if you want) ----
set "API_PORT=5050"
set "VLLM_PORT=8000"
set "MODEL_ID=TinyLlama/TinyLlama-1.1B-Chat-v1.0"

REM Optional: set your WSL distro name if not the default (e.g., Ubuntu-22.04). Leave empty to use the default distro
set "WSL_DISTRO="
REM Optional: keep this parent window open after launching children (so you can read any messages)
set "KEEP_PARENT_OPEN=1"

REM WSL Linux path to your repo (as seen inside Ubuntu)
set "WSL_PROJECT_PATH=/Projects/Doma Backend/Program/ai-backend"

REM UNC path to the same folder (as seen from Windows)
set "UNC_PROJECT_PATH=\\wsl.localhost\Ubuntu\Projects\Doma Backend\Program\ai-backend"

REM Windows venv for the gateway (kept on Windows, not inside WSL)
set "GW_VENV=%USERPROFILE%\ai-backend-gateway-venv"

echo.
echo [preflight] Checking tools on Windows...
where wsl.exe >nul 2>nul || (
  echo [error] "wsl.exe" not found. Please enable Windows Subsystem for Linux and install a distro from Microsoft Store.
  echo         See: "Turn Windows features on or off" > Windows Subsystem for Linux.
  goto :fail_pause
)
where powershell.exe >nul 2>nul || (
  echo [error] "powershell.exe" not found. Unexpected Windows configuration.
  goto :fail_pause
)
where py.exe >nul 2>nul || (
  echo [warning] Python launcher (py.exe) not found. Trying plain python instead.
  set "PY_LAUNCH=python"
)
if not defined PY_LAUNCH set "PY_LAUNCH=py -3"

echo.
echo [preflight] Detecting WSL distros (for reference):
wsl -l -q 2>nul || echo   (could not list distros)

echo.
echo [preflight] Checking UNC path: %UNC_PROJECT_PATH%
if not exist "%UNC_PROJECT_PATH%\requirements.txt" (
  echo [warn] UNC path not accessible at: %UNC_PROJECT_PATH%
  set "ALT_UNC_PROJECT_PATH=%UNC_PROJECT_PATH:\wsl.localhost=\\wsl$%"
  echo [preflight] Trying fallback UNC path: %ALT_UNC_PROJECT_PATH%
  if exist "%ALT_UNC_PROJECT_PATH%\requirements.txt" (
    echo [ok] Using fallback UNC path.
    set "UNC_PROJECT_PATH=%ALT_UNC_PROJECT_PATH%"
  ) else (
    echo [error] Can't find requirements.txt at either path.
    echo         Update UNC_PROJECT_PATH in this script to point at your ai-backend folder.
    echo         If your WSL distro name is not "Ubuntu" (e.g., "Ubuntu-22.04"), the UNC path will differ.
    echo         Example: \\wsl.localhost\Ubuntu-22.04\Projects\Doma Backend\Program\ai-backend
    goto :fail_pause
  )
)

echo.
set "WSL_LABEL=default WSL distro"
if not "%WSL_DISTRO%"=="" set "WSL_LABEL=%WSL_DISTRO%"
set "WSL_D_FLAG="
if not "%WSL_DISTRO%"=="" set "WSL_D_FLAG=-d %WSL_DISTRO%"

echo [1/2] Starting vLLM in WSL (%WSL_LABEL%) on port %VLLM_PORT% serving model "%MODEL_ID%"...
start "AI Server (WSL vLLM)" wsl.exe %WSL_D_FLAG% -- bash -lc "export DEBIAN_FRONTEND=noninteractive; ( \
  set -euo pipefail; \
  sudo apt-get update -y >/dev/null && sudo apt-get install -y python3 python3-venv python3-pip >/dev/null; \
  cd '%WSL_PROJECT_PATH%'; \
  if [ ! -d .vllm-venv ]; then python3 -m venv .vllm-venv; fi; \
  source .vllm-venv/bin/activate; \
  python -m pip install -q --upgrade pip; \
  python -m pip install -q vllm; \
  python -m vllm.entrypoints.openai.api_server --model '%MODEL_ID%' --host 0.0.0.0 --port %VLLM_PORT% --served-model-name '%MODEL_ID%' \
) || { status=$?; echo; echo 'vLLM startup failed (exit code' $status ')'; echo 'Check model id or vLLM install.'; read -n 1 -s -r -p 'Press any key to close...'; }"

echo.
echo [2/2] Starting Gateway on Windows (port %API_PORT%) pointing to http://localhost:%VLLM_PORT%/v1 ...
set "VLLM_BASE_URL=http://localhost:%VLLM_PORT%/v1"
REM Launch the gateway in a PowerShell window for robust quoting
start "Gateway (Windows)" powershell -NoExit -Command "$env:API_PORT='%API_PORT%'; $env:VLLM_BASE_URL='%VLLM_BASE_URL%'; if (!(Test-Path '%GW_VENV%\Scripts\Activate.ps1')) { %PY_LAUNCH% -m venv '%GW_VENV%' }; & '%GW_VENV%\Scripts\Activate.ps1'; pip install -q --upgrade pip; pip install -q -r '%UNC_PROJECT_PATH%\requirements.txt'; $env:PYTHONPATH='%UNC_PROJECT_PATH%'; uvicorn app.main:app --host 0.0.0.0 --port $env:API_PORT"

echo.
echo Launched both windows:
echo - vLLM (WSL) on http://localhost:%VLLM_PORT%/v1
echo - Gateway (Windows) on http://localhost:%API_PORT%
echo.
echo Health:   http://localhost:%API_PORT%/health
echo Models:   http://localhost:%API_PORT%/api/models
echo.
if defined KEEP_PARENT_OPEN (
  echo Press any key to close this window...
  pause >nul
)
endlocal

:fail_pause
echo.
echo Press any key to close this window...
pause >nul
goto :eof