@echo off
echo.
echo This script must be run from a regular Command Prompt, not by double-clicking.
echo.
echo Instructions:
echo 1. Press Win+R, type "cmd", press Enter
echo 2. Copy and paste this command:
echo.
echo    pushd "\\wsl.localhost\Ubuntu\Projects\Doma Backend\Program\ai-backend" ^&^& run-from-cmd.bat
echo.
echo 3. Press Enter
echo.
echo This will map the UNC path to a drive letter and avoid execution issues.
echo.

REM If we get here via pushd, the current directory will be mapped to a drive
if "%CD:~1,1%"==":" (
    echo Great! Running from mapped drive: %CD%
    echo.
    echo Now testing the main script...
    call start-backend.bat
) else (
    echo Still on UNC path: %CD%
    echo Please follow the instructions above.
)

echo.
pause
