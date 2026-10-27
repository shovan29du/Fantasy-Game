@echo off
setlocal
title Worldweaver Multiverse Tabletop
cd /d "%~dp0"

:: ── Python detection ─────────────────────────────────────────────────────
set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

"%PYTHON_EXE%" --version >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python was not found.
    echo         Run install_windows.bat first, or install Python 3.10+ from
    echo         https://python.org and check "Add Python to PATH".
    pause
    exit /b 1
)

:: ── Install / update dependencies ────────────────────────────────────────
echo.
echo   Checking and installing dependencies from requirements.txt ...
echo.
"%PYTHON_EXE%" -m pip install --upgrade pip --quiet
"%PYTHON_EXE%" -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Dependency installation failed. See the output above for details.
    pause
    exit /b 1
)

:: ── Kill any previous instance on port 8501 ──────────────────────────────
echo   Closing any previous instance on port 8501 ...
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8501 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>nul
)
timeout /t 2 /nobreak >nul

:: ── Launch ────────────────────────────────────────────────────────────────
echo.
echo   ╔══════════════════════════════════════════════════════╗
echo   ║   Worldweaver Multiverse Tabletop                    ║
echo   ║   http://localhost:8501                              ║
echo   ║                                                      ║
echo   ║   Start LM Studio on port 1234 for AI chat.         ║
echo   ║   Close this window to stop the server.             ║
echo   ╚══════════════════════════════════════════════════════╝
echo.

start "" "http://127.0.0.1:8501"
"%PYTHON_EXE%" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8501

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Worldweaver exited with an error. Check logs\aichat_pro.log for details.
)
pause
