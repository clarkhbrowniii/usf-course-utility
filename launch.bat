@echo off
title USF Course Utility

REM Move to the directory containing this batch file
cd /d "%~dp0"

REM Verify virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo ERROR: Python virtual environment not found.
    echo Expected: .venv\Scripts\python.exe
    echo.
    pause
    exit /b 1
)

echo Starting USF Course Utility...

REM Open the application in the default browser after a short delay
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:5000"

REM Run Flask using the project's virtual environment
".venv\Scripts\python.exe" app.py

echo.
echo USF Course Utility has stopped.
pause