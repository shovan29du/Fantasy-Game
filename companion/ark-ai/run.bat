@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  echo First run setup: creating virtual environment...
  set "PYTHON="
  where py >nul 2>nul
  if !errorlevel!==0 (
    py -3 -c "import sys" >nul 2>nul
    if !errorlevel!==0 set "PYTHON=py -3"
  )
  if not defined PYTHON (
    where python >nul 2>nul
    if !errorlevel!==0 (
      python -c "import sys" >nul 2>nul
      if !errorlevel!==0 set "PYTHON=python"
    )
  )
  if not defined PYTHON (
    echo Python 3 was not found. Install it from https://www.python.org/downloads/
    start "" "https://www.python.org/downloads/"
    pause
    exit /b 1
  )
  !PYTHON! -m venv venv
  if errorlevel 1 ( echo Could not create venv. & pause & exit /b 1 )
  "venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>nul
  "venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 ( echo Dependency install failed. & pause & exit /b 1 )
)
"venv\Scripts\python.exe" -c "import db; db.init_db()"
if errorlevel 1 ( echo Database setup failed. & pause & exit /b 1 )
echo Ark_AI is running. Close this window to stop it.
"venv\Scripts\python.exe" "app.py"
