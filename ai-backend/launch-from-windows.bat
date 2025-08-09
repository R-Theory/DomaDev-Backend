@echo off
REM This launcher works around UNC path issues by copying the main script to Windows temp

echo Launching AI Backend from UNC path workaround...

REM Create temp directory for the script
set "TEMP_SCRIPT=%TEMP%\ai-backend-launcher.bat"

REM Copy the main script to Windows temp (this avoids UNC execution issues)
copy "%~dp0start-backend.bat" "%TEMP_SCRIPT%" >nul

REM Run from the temp location
"%TEMP_SCRIPT%"

REM Clean up
del "%TEMP_SCRIPT%" 2>nul

pause
