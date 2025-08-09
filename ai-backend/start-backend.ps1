# PowerShell version of the launcher - handles UNC paths better than batch files

# ---- Config (edit these if you want) ----
$API_PORT = "5050"
$VLLM_PORT = "8000"
$MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# Optional: set your WSL distro name if not the default (e.g., Ubuntu-22.04). Leave empty to use the default distro
$WSL_DISTRO = ""

# WSL Linux path to your repo (as seen inside Ubuntu)
$WSL_PROJECT_PATH = "/Projects/Doma Backend/Program/ai-backend"

# UNC path to the same folder (as seen from Windows)
$UNC_PROJECT_PATH = "\\wsl.localhost\Ubuntu\Projects\Doma Backend\Program\ai-backend"

# Windows venv for the gateway (kept on Windows, not inside WSL)
$GW_VENV = "$env:USERPROFILE\ai-backend-gateway-venv"

Write-Host ""
Write-Host "[preflight] Checking tools on Windows..." -ForegroundColor Yellow

# Check for WSL
if (!(Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    Write-Host "[error] wsl.exe not found. Please enable Windows Subsystem for Linux." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check for Python
$pythonCmd = "py"
if (!(Get-Command py.exe -ErrorAction SilentlyContinue)) {
    Write-Host "[warning] Python launcher (py.exe) not found. Trying python instead." -ForegroundColor Yellow
    $pythonCmd = "python"
    if (!(Get-Command python.exe -ErrorAction SilentlyContinue)) {
        Write-Host "[error] Python not found. Please install Python from python.org" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "[preflight] Detecting WSL distros:" -ForegroundColor Yellow
try {
    wsl -l -q
} catch {
    Write-Host "  (could not list distros)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[preflight] Checking UNC path: $UNC_PROJECT_PATH" -ForegroundColor Yellow
if (!(Test-Path "$UNC_PROJECT_PATH\requirements.txt")) {
    $altPath = $UNC_PROJECT_PATH -replace "\\wsl\.localhost", "\\wsl$"
    Write-Host "[warn] UNC path not accessible. Trying fallback: $altPath" -ForegroundColor Yellow
    if (Test-Path "$altPath\requirements.txt") {
        Write-Host "[ok] Using fallback UNC path." -ForegroundColor Green
        $UNC_PROJECT_PATH = $altPath
    } else {
        Write-Host "[error] Can't find requirements.txt at either path." -ForegroundColor Red
        Write-Host "        Update UNC_PROJECT_PATH in this script." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Set up WSL command
$wslLabel = if ($WSL_DISTRO) { $WSL_DISTRO } else { "default WSL distro" }
$wslCmd = if ($WSL_DISTRO) { "wsl.exe -d $WSL_DISTRO" } else { "wsl.exe" }

Write-Host ""
Write-Host "[1/2] Starting vLLM in WSL ($wslLabel) on port $VLLM_PORT serving model `"$MODEL_ID`"..." -ForegroundColor Cyan

$vllmScript = @"
export DEBIAN_FRONTEND=noninteractive
(
  set -euo pipefail
  sudo apt-get update -y >/dev/null && sudo apt-get install -y python3 python3-venv python3-pip >/dev/null
  cd '$WSL_PROJECT_PATH'
  if [ ! -d .vllm-venv ]; then python3 -m venv .vllm-venv; fi
  source .vllm-venv/bin/activate
  python -m pip install -q --upgrade pip
  python -m pip install -q vllm
  python -m vllm.entrypoints.openai.api_server --model '$MODEL_ID' --host 0.0.0.0 --port $VLLM_PORT --served-model-name '$MODEL_ID'
) || {
  status=`$?
  echo
  echo "vLLM startup failed (exit code `$status)"
  echo "Check model id or vLLM install."
  read -n 1 -s -r -p "Press any key to close..."
}
"@

Start-Process -FilePath "wsl.exe" -ArgumentList @($WSL_DISTRO ? @("-d", $WSL_DISTRO, "--", "bash", "-lc", $vllmScript) : @("--", "bash", "-lc", $vllmScript)) -WindowStyle Normal

Write-Host ""
Write-Host "[2/2] Starting Gateway on Windows (port $API_PORT) pointing to http://localhost:$VLLM_PORT/v1 ..." -ForegroundColor Cyan

$gatewayScript = @"
`$env:API_PORT='$API_PORT'
`$env:VLLM_BASE_URL='http://localhost:$VLLM_PORT/v1'
if (!(Test-Path '$GW_VENV\Scripts\Activate.ps1')) { 
    $pythonCmd -m venv '$GW_VENV' 
}
& '$GW_VENV\Scripts\Activate.ps1'
pip install -q --upgrade pip
pip install -q -r '$UNC_PROJECT_PATH\requirements.txt'
`$env:PYTHONPATH='$UNC_PROJECT_PATH'
uvicorn app.main:app --host 0.0.0.0 --port `$env:API_PORT
"@

Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-Command", $gatewayScript) -WindowStyle Normal

Write-Host ""
Write-Host "Launched both windows:" -ForegroundColor Green
Write-Host "- vLLM (WSL) on http://localhost:$VLLM_PORT/v1" -ForegroundColor Green
Write-Host "- Gateway (Windows) on http://localhost:$API_PORT" -ForegroundColor Green
Write-Host ""
Write-Host "Health:   http://localhost:$API_PORT/health" -ForegroundColor Cyan
Write-Host "Models:   http://localhost:$API_PORT/api/models" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to close this window"
