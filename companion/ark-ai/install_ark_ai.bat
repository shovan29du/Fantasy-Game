REM ============================================================
REM  Ark_Ai - Windows Installer
REM ============================================================
REM  Sets up a Python virtual environment, installs dependencies,
REM  initializes the database, writes a local .env config, and
REM  creates Desktop / Start Menu shortcuts. Safe to re-run.
REM
REM  Does NOT require administrator rights.
REM ============================================================
@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ============================================================
echo   Ark_Ai - Windows Installer
echo ============================================================
echo Installing into: %cd%
echo.

if not exist "app.py" (
    echo ERROR: app.py not found in this folder.
    echo Run this installer from inside the Ark_Ai project folder.
    pause
    exit /b 1
)

rem ---------------------------------------------------------------
rem 1. Find a Python interpreter: py launcher, then python, then python3
rem ---------------------------------------------------------------
set "PYTHON="

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 -c "import sys" >nul 2>nul
    if %errorlevel%==0 set "PYTHON=py -3"
)

if not defined PYTHON (
    where python >nul 2>nul
    if %errorlevel%==0 (
        python -c "import sys" >nul 2>nul
        if %errorlevel%==0 set "PYTHON=python"
    )
)

if not defined PYTHON (
    where python3 >nul 2>nul
    if %errorlevel%==0 (
        python3 -c "import sys" >nul 2>nul
        if %errorlevel%==0 set "PYTHON=python3"
    )
)

if not defined PYTHON (
    echo ERROR: No working Python interpreter was found.
    echo Tried: py launcher, python, python3
    echo.
    echo Install Python 3.10+ from https://www.python.org/downloads/
    echo and make sure "Add python.exe to PATH" is checked, then re-run
    echo this installer.
    pause
    exit /b 1
)
echo Using Python: %PYTHON%

rem ---------------------------------------------------------------
rem 2. Create the virtual environment if missing
rem ---------------------------------------------------------------
if exist "venv\Scripts\python.exe" (
    echo Virtual environment already exists - skipping creation.
) else (
    echo Creating virtual environment in .\venv ...
    %PYTHON% -m venv venv
    if errorlevel 1 (
        echo ERROR: failed to create the virtual environment.
        pause
        exit /b 1
    )
)

set "VENV_PY=venv\Scripts\python.exe"
set "VENV_PIP=venv\Scripts\pip.exe"

if not exist "%VENV_PY%" (
    echo ERROR: virtual environment looks broken ^(missing %VENV_PY%^).
    echo Delete the venv folder and re-run this installer.
    pause
    exit /b 1
)

rem ---------------------------------------------------------------
rem 3. Install dependencies
rem ---------------------------------------------------------------
echo.
echo Upgrading pip...
"%VENV_PY%" -m pip install --upgrade pip >nul 2>nul

echo Installing core requirements (requirements.txt)...
"%VENV_PIP%" install -r requirements.txt
if errorlevel 1 (
    echo ERROR: failed to install requirements.txt. See output above.
    pause
    exit /b 1
)

set "DEV_ANSWER="
set /p DEV_ANSWER="Install developer/test dependencies for running pytest? [y/N]: "
if /i "%DEV_ANSWER%"=="y" (
    echo Installing developer requirements (requirements-dev.txt)...
    "%VENV_PIP%" install -r requirements-dev.txt
    if errorlevel 1 (
        echo WARNING: failed to install requirements-dev.txt - continuing anyway.
    )
)

rem ---------------------------------------------------------------
rem 4. PostgreSQL vs SQLite
rem ---------------------------------------------------------------
set "USE_PG=n"
set "DATABASE_URL_INPUT="

if defined DATABASE_URL (
    echo DATABASE_URL is already set in this shell - using PostgreSQL.
    set "USE_PG=y"
    set "DATABASE_URL_INPUT=%DATABASE_URL%"
) else (
    set "PG_ANSWER="
    set /p PG_ANSWER="Use PostgreSQL instead of the default SQLite file? [y/N]: "
    if /i "%PG_ANSWER%"=="y" set "USE_PG=y"
)

if /i "%USE_PG%"=="y" (
    echo Installing PostgreSQL driver (requirements-postgres.txt)...
    "%VENV_PIP%" install -r requirements-postgres.txt
    if errorlevel 1 (
        echo ERROR: failed to install the PostgreSQL driver.
        pause
        exit /b 1
    )
    if not defined DATABASE_URL_INPUT (
        set /p DATABASE_URL_INPUT="Enter DATABASE_URL (postgresql://user:pass@host:5432/dbname): "
    )
)

rem ---------------------------------------------------------------
rem 5. Network exposure: localhost-only or LAN/network
rem ---------------------------------------------------------------
echo.
echo Ark_Ai can run in two modes:
echo   1. Localhost only  (recommended - only this PC can reach it)
echo   2. Network exposed  (other devices on your network can connect)
set "NET_ANSWER="
set /p NET_ANSWER="Expose Ark_Ai to the network instead of localhost only? [y/N]: "

set "ARK_AI_HOST_VALUE=127.0.0.1"
set "ARK_AI_TOKEN_VALUE="

if /i "%NET_ANSWER%"=="y" (
    set "ARK_AI_HOST_VALUE=0.0.0.0"
    echo.
    echo Network exposure requires a shared access token ^(ARK_AI_TOKEN^).
    set "TOKEN_ANSWER="
    set /p TOKEN_ANSWER="Enter an ARK_AI_TOKEN value, or leave blank to auto-generate one: "
    if defined TOKEN_ANSWER (
        set "ARK_AI_TOKEN_VALUE=%TOKEN_ANSWER%"
    ) else (
        for /f "usebackq delims=" %%T in (`"%VENV_PY%" -c "import secrets; print(secrets.token_hex(24))"`) do set "ARK_AI_TOKEN_VALUE=%%T"
        echo Generated ARK_AI_TOKEN: !ARK_AI_TOKEN_VALUE!
    )
)

rem ---------------------------------------------------------------
rem 6. ARK_AI_SECRET_KEY - generate one if .env doesn't already have it
rem ---------------------------------------------------------------
set "EXISTING_SECRET="
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"ARK_AI_SECRET_KEY=" ".env"`) do set "EXISTING_SECRET=%%B"
)

if defined EXISTING_SECRET (
    set "SECRET_KEY_VALUE=%EXISTING_SECRET%"
    echo Reusing existing ARK_AI_SECRET_KEY from .env
) else (
    for /f "usebackq delims=" %%S in (`"%VENV_PY%" -c "import secrets; print(secrets.token_hex(32))"`) do set "SECRET_KEY_VALUE=%%S"
    echo Generated a new ARK_AI_SECRET_KEY.
)

rem ---------------------------------------------------------------
rem 7. Write .env (only if it doesn't exist yet - never overwrite silently)
rem ---------------------------------------------------------------
if exist ".env" (
    echo .env already exists - leaving it untouched.
    echo   (delete .env and re-run this installer to regenerate it)
) else (
    echo Writing .env ...
    (
        echo # Ark_Ai local configuration - generated by install_ark_ai.bat
        echo # This file is gitignored and must never be committed.
        echo ARK_AI_SECRET_KEY=%SECRET_KEY_VALUE%
        echo ARK_AI_HOST=%ARK_AI_HOST_VALUE%
        echo ARK_AI_PORT=5000
        if defined ARK_AI_TOKEN_VALUE echo ARK_AI_TOKEN=%ARK_AI_TOKEN_VALUE%
        if defined DATABASE_URL_INPUT echo DATABASE_URL=%DATABASE_URL_INPUT%
    ) > ".env"
)

rem ---------------------------------------------------------------
rem 8. Initialize the database / run migrations
rem ---------------------------------------------------------------
echo.
echo Initializing database (running migrations)...
if defined DATABASE_URL_INPUT set "DATABASE_URL=%DATABASE_URL_INPUT%"
"%VENV_PY%" -c "import db; db.init_db(); print('Database ready at:', db.DATABASE_URL or db.DB_PATH)"
if errorlevel 1 (
    echo ERROR: database initialization failed. See output above.
    pause
    exit /b 1
)

rem ---------------------------------------------------------------
rem 9. Shortcuts (Desktop - preferring OneDrive Desktop - and Start Menu)
rem ---------------------------------------------------------------
echo.
echo Creating Desktop and Start Menu shortcuts...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create_shortcuts.ps1" -ProjectDir "%~dp0"
if errorlevel 1 (
    echo WARNING: shortcut creation reported an error - you can still run
    echo Ark_Ai directly with run_ark_ai.bat.
)

rem ---------------------------------------------------------------
rem 10. Done
rem ---------------------------------------------------------------
echo.
echo ============================================================
echo   Install complete!
echo ============================================================
echo Launcher:      run_ark_ai.bat
echo Desktop/Start: Ark_Ai.lnk shortcuts were created if possible.
if /i "%NET_ANSWER%"=="y" (
    echo Mode:          network-exposed ^(0.0.0.0^) - ARK_AI_TOKEN required
    echo URL:           http://YOUR-PC-IP:5000  ^(also http://127.0.0.1:5000 locally^)
) else (
    echo Mode:          localhost-only
    echo URL:           http://127.0.0.1:5000
)
echo.
echo Run Ark_Ai any time with: run_ark_ai.bat
echo (or double-click the Ark_Ai shortcut on your Desktop / Start Menu)
echo ============================================================
pause
exit /b 0

