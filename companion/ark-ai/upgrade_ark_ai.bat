REM ============================================================
REM  Ark_Ai - Upgrade Helper
REM ============================================================
REM  Run this from the NEW Ark_Ai folder to upgrade an EXISTING
REM  Ark_Ai folder without overwriting local user data:
REM    - .env
REM    - config.json
REM    - ark_ai.db / realzip.db
REM    - workspace
REM    - venv
REM
REM  Usage:
REM    upgrade_ark_ai.bat "C:\path\to\existing\Ark_Ai"
REM
REM  If no path is passed, the script asks for it.
REM ============================================================
@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"
set "SOURCE_DIR=%cd%"
set "TARGET_DIR=%~1"

if not exist "%SOURCE_DIR%\app.py" (
    echo ERROR: app.py not found in this new Ark_Ai folder.
    pause
    exit /b 1
)

if not defined TARGET_DIR (
    echo.
    echo Enter the existing Ark_Ai folder to upgrade.
    echo Example: C:\Users\you\Documents\Ark_Ai
    set /p TARGET_DIR="Existing Ark_Ai folder: "
)

if not defined TARGET_DIR (
    echo ERROR: no target folder was provided.
    pause
    exit /b 1
)

if not exist "%TARGET_DIR%\app.py" (
    echo ERROR: target folder does not look like Ark_Ai:
    echo   %TARGET_DIR%
    echo app.py was not found there.
    pause
    exit /b 1
)

for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"`) do set "STAMP=%%T"
set "BACKUP_DIR=%TARGET_DIR%\_upgrade_backup_%STAMP%"

echo.
echo ============================================================
echo   Upgrading Ark_Ai
echo ============================================================
echo New files from: %SOURCE_DIR%
echo Existing app:   %TARGET_DIR%
echo Backup folder:  %BACKUP_DIR%
echo.
echo Close any running Ark_Ai window before continuing.
choice /c YN /m "Continue with upgrade"
if errorlevel 2 (
    echo Upgrade cancelled.
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$src=$env:SOURCE_DIR; $dst=$env:TARGET_DIR; $backup=$env:BACKUP_DIR;" ^
  "New-Item -ItemType Directory -Force -Path $backup | Out-Null;" ^
  "$preserveFiles=@('.env','config.json','ark_ai.db','realzip.db');" ^
  "foreach($name in $preserveFiles){ $p=Join-Path $dst $name; if(Test-Path -LiteralPath $p){ Copy-Item -LiteralPath $p -Destination $backup -Force } }" ^
  "foreach($name in @('workspace','venv')){ $p=Join-Path $dst $name; if(Test-Path -LiteralPath $p){ Copy-Item -LiteralPath $p -Destination (Join-Path $backup $name) -Recurse -Force } }" ^
  "$excludeDirs=@('venv','workspace','.pytest_cache','__pycache__');" ^
  "$excludeFiles=@('.env','config.json','ark_ai.db','realzip.db');" ^
  "Get-ChildItem -LiteralPath $src -Force | ForEach-Object {" ^
  "  if($_.PSIsContainer){" ^
  "    if($excludeDirs -notcontains $_.Name -and -not $_.Name.StartsWith('_upgrade_backup_')){ Copy-Item -LiteralPath $_.FullName -Destination $dst -Recurse -Force }" ^
  "  } else {" ^
  "    if($excludeFiles -notcontains $_.Name -and $_.Extension -ne '.pyc'){ Copy-Item -LiteralPath $_.FullName -Destination $dst -Force }" ^
  "  }" ^
  "};" ^
  "foreach($name in $preserveFiles){ $p=Join-Path $backup $name; if(Test-Path -LiteralPath $p){ Copy-Item -LiteralPath $p -Destination $dst -Force } }" ^
  "foreach($name in @('workspace','venv')){ $p=Join-Path $backup $name; if(Test-Path -LiteralPath $p){ Copy-Item -LiteralPath $p -Destination (Join-Path $dst $name) -Recurse -Force } }"

if errorlevel 1 (
    echo.
    echo ERROR: upgrade copy failed. Your backup is here:
    echo   %BACKUP_DIR%
    pause
    exit /b 1
)

if exist "%TARGET_DIR%\venv\Scripts\python.exe" (
    echo.
    echo Updating dependencies and database...
    "%TARGET_DIR%\venv\Scripts\python.exe" -m pip install -r "%TARGET_DIR%\requirements.txt"
    if errorlevel 1 echo WARNING: dependency update failed. run_ark_ai.bat will try again later.
    "%TARGET_DIR%\venv\Scripts\python.exe" -c "import sys; sys.path.insert(0, r'%TARGET_DIR%'); import db; db.init_db(); print('Database upgraded')"
    if errorlevel 1 echo WARNING: database migration failed. run_ark_ai.bat will try again later.
)

echo.
echo ============================================================
echo   Upgrade complete.
echo ============================================================
echo Preserved user data and backup:
echo   %BACKUP_DIR%
echo.
echo Start Ark_Ai from the upgraded folder:
echo   %TARGET_DIR%\run_ark_ai.bat
echo ============================================================
pause
exit /b 0
