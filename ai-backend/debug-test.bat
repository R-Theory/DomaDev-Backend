@echo off
echo.
echo ========== DEBUG TEST ==========
echo This window will stay open so you can read any errors.
echo.
echo Current directory: %CD%
echo Script location: %~dp0
echo.
echo Testing basic commands:
echo.

echo [1] Testing WSL...
where wsl.exe >nul 2>nul
if errorlevel 1 (
    echo ERROR: WSL not found
) else (
    echo OK: WSL found
    wsl --version 2>nul || echo WSL version check failed
)

echo.
echo [2] Testing Python...
where py.exe >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python launcher not found
    where python.exe >nul 2>nul
    if errorlevel 1 (
        echo ERROR: Python also not found
    ) else (
        echo OK: Python found (no launcher)
    )
) else (
    echo OK: Python launcher found
)

echo.
echo [3] Testing UNC path...
set "TEST_UNC=\\wsl.localhost\Ubuntu\Projects\Doma Backend\Program\ai-backend"
echo Checking: %TEST_UNC%
if exist "%TEST_UNC%" (
    echo OK: UNC path exists
    if exist "%TEST_UNC%\requirements.txt" (
        echo OK: requirements.txt found
    ) else (
        echo ERROR: requirements.txt not found
    )
) else (
    echo ERROR: UNC path not accessible
    echo Trying fallback...
    set "TEST_UNC=\\wsl$\Ubuntu\Projects\Doma Backend\Program\ai-backend"
    echo Checking: %TEST_UNC%
    if exist "%TEST_UNC%" (
        echo OK: Fallback UNC path exists
    ) else (
        echo ERROR: Fallback UNC path also not accessible
    )
)

echo.
echo [4] Testing WSL distros...
wsl -l -q 2>nul || echo ERROR: Cannot list WSL distros

echo.
echo ========== END DEBUG ==========
echo.
echo This window will stay open until you press a key.
echo If you saw any errors above, please share them.
pause
