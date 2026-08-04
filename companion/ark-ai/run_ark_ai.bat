REM ============================================================
REM  Ark_Ai - Launcher
REM ============================================================
REM  Activates the virtual environment, loads .env, and starts
REM  app.py. The window stays open if the app crashes so the
REM  error is readable.
REM ============================================================
@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

if not exist "app.py" (
    echo ERROR: app.py not found in this folder.
    echo This launcher must stay inside the Ark_Ai project folder.
    pause
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    echo Virtual environment not found - setting it up now.
    echo This happens the first time you run Ark_Ai from the zip.
    echo.

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
        where python3 >nul 2>nul
        if !errorlevel!==0 (
            python3 -c "import sys" >nul 2>nul
            if !errorlevel!==0 set "PYTHON=python3"
        )
    )

    if not defined PYTHON (
        echo ERROR: Python 3 was not found.
        echo Install Python 3.10+ from https://www.python.org/downloads/
        echo Check "Add python.exe to PATH", then run this file again.
        start "" "https://www.python.org/downloads/"
        pause
        exit /b 1
    )

    echo Creating virtual environment with !PYTHON! ...
    !PYTHON! -m venv venv
    if errorlevel 1 (
        echo ERROR: could not create the virtual environment.
        pause
        exit /b 1
    )

    echo Installing Ark_Ai requirements ...
    "venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>nul
    "venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: dependency install failed. Check your internet connection and try again.
        pause
        exit /b 1
    )
)

echo Checking database ...
"venv\Scripts\python.exe" -c "import db; db.init_db(); print('Database ready')"
if errorlevel 1 (
    echo ERROR: database initialization failed.
    pause
    exit /b 1
)

rem ---- load .env (KEY=VALUE per line, '#' comments and blank lines ignored) ----
if exist ".env" (
    for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
        if not "%%A"=="" if not "%%B"=="" set "%%A=%%B"
    )
) else (
    echo WARNING: .env not found - using built-in defaults (localhost only,
    echo a random session secret that changes every restart). Run
    echo install_ark_ai.bat to generate a persistent .env.
)

echo ============================================================
echo   Starting Ark_Ai ...
echo ============================================================

"venv\Scripts\python.exe" app.py
set "EXITCODE=%errorlevel%"

if not "%EXITCODE%"=="0" (
    echo.
    echo ============================================================
    echo   Ark_Ai exited with an error ^(code %EXITCODE%^).
    echo   Scroll up to see what went wrong.
    echo ============================================================
)

pause
exit /b %EXITCODE%

