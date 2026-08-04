@echo off
setlocal
title Worldweaver Multiverse Tabletop
cd /d "%~dp0"

set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

"%PYTHON_EXE%" --version >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found.
    echo         Run install_windows.bat or install Python 3.10+ from https://python.org.
    pause
    exit /b 1
)

echo.
echo   Installing required dependencies from requirements.txt ...
echo.
"%PYTHON_EXE%" -m pip install --upgrade pip --quiet
"%PYTHON_EXE%" -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Dependency installation failed. See the output above for details.
    pause
    exit /b 1
)

echo   Closing previous instance on port 8501 if any...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8501" ^| findstr "LISTENING"') do taskkill /PID %%a /F >nul 2>nul
timeout /t 2 /nobreak >nul

echo.
echo   Worldweaver Multiverse Tabletop starting on http://localhost:8501
echo   Frontend: React. Backend: FastAPI.
echo   Browser will open automatically.
echo   Start LM Studio's local server first if you want local LLM chat.
echo.
start "" "http://127.0.0.1:8501"
"%PYTHON_EXE%" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8501
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Worldweaver Multiverse Tabletop exited with an error. See logs\aichat_pro.log for details.
)
pause
