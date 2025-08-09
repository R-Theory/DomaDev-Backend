@echo off
echo Copying AI Backend launcher to Windows temp and running...
echo.

REM Create a temp directory on Windows
set "TEMP_DIR=%TEMP%\ai-backend-launcher"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

REM Copy the main script to Windows temp
copy "%~dp0start-backend.bat" "%TEMP_DIR%\start-backend.bat" >nul

REM Copy this script's directory path for the main script to use
echo set "ORIGINAL_UNC_PATH=%~dp0" > "%TEMP_DIR%\original-path.bat"

REM Change to temp directory and run
pushd "%TEMP_DIR%"
echo Running from: %CD%
echo.

REM Modify the start-backend.bat to use the original UNC path
powershell -Command "(Get-Content 'start-backend.bat') -replace 'set \"UNC_PROJECT_PATH=.*\"', 'call original-path.bat & set \"UNC_PROJECT_PATH=%%ORIGINAL_UNC_PATH%%\"' | Set-Content 'start-backend-fixed.bat'"

REM Run the fixed version
start-backend-fixed.bat

REM Clean up
popd
rmdir /s /q "%TEMP_DIR%" 2>nul

pause
