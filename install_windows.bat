@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.10+ is required. Install it from https://python.org and enable "Add Python to PATH".
    pause
    exit /b 1
)
if /I "%~1"=="all" (
    python full_install.py --all-optional
) else if /I "%~1"=="minimal" (
    python full_install.py --minimal
) else (
    python full_install.py
)
pause
