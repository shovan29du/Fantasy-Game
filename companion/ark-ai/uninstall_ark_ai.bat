REM ============================================================
REM  Ark_Ai - Uninstaller
REM ============================================================
REM  Removes shortcuts created by the installer. Asks before
REM  touching the virtual environment or database files, and
REM  NEVER deletes the project source code unless you explicitly
REM  confirm it by typing DELETE.
REM ============================================================
@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ============================================================
echo   Ark_Ai - Uninstaller
echo ============================================================
echo.

rem ---------------------------------------------------------------
rem 1. Remove Desktop shortcut (OneDrive Desktop first, then normal Desktop)
rem ---------------------------------------------------------------
set "REMOVED_ANY=0"

for %%S in (
    "%USERPROFILE%\OneDrive\Desktop\Ark_Ai.lnk"
    "%USERPROFILE%\Desktop\Ark_Ai.lnk"
    "%OneDrive%\Desktop\Ark_Ai.lnk"
    "%OneDriveCommercial%\Desktop\Ark_Ai.lnk"
) do (
    if exist %%S (
        del /f /q %%S
        echo Removed Desktop shortcut: %%S
        set "REMOVED_ANY=1"
    )
)
if "%REMOVED_ANY%"=="0" echo No Desktop shortcut found.

rem ---------------------------------------------------------------
rem 2. Remove Start Menu shortcut
rem ---------------------------------------------------------------
for %%S in (
    "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Ark_Ai.lnk"
) do (
    if exist %%S (
        del /f /q %%S
        echo Removed Start Menu shortcut: %%S
    )
)

rem ---------------------------------------------------------------
rem 3. Virtual environment (ask first)
rem ---------------------------------------------------------------
echo.
if exist "venv" (
    set "DEL_VENV="
    set /p DEL_VENV="Delete the virtual environment folder .\venv ? [y/N]: "
    if /i "!DEL_VENV!"=="y" (
        rmdir /s /q "venv"
        echo Deleted .\venv
    ) else (
        echo Keeping .\venv
    )
) else (
    echo No .\venv folder found.
)

rem ---------------------------------------------------------------
rem 4. Database files (ask first) - SQLite file(s) only, never source code
rem ---------------------------------------------------------------
echo.
set "FOUND_DB=0"
for %%F in (*.db) do set "FOUND_DB=1"
if "%FOUND_DB%"=="1" (
    set "DEL_DB="
    set /p DEL_DB="Delete local SQLite database file(s) (*.db)? This deletes all conversations. [y/N]: "
    if /i "!DEL_DB!"=="y" (
        del /f /q *.db
        echo Deleted *.db
    ) else (
        echo Keeping database file(s).
    )
) else (
    echo No local *.db file found ^(nothing to delete, or you are using PostgreSQL^).
)

rem ---------------------------------------------------------------
rem 5. Local config (.env / config.json) - ask first
rem ---------------------------------------------------------------
echo.
if exist ".env" (
    set "DEL_ENV="
    set /p DEL_ENV="Delete local .env config (secret key, tokens, DATABASE_URL)? [y/N]: "
    if /i "!DEL_ENV!"=="y" (
        del /f /q ".env"
        echo Deleted .env
    )
)

rem ---------------------------------------------------------------
rem 6. Source code - NEVER deleted unless explicitly confirmed
rem ---------------------------------------------------------------
echo.
echo The project source code (app.py, db.py, templates\, etc.) has NOT
echo been touched. To remove it as well, you must confirm explicitly.
set "DEL_SOURCE="
set /p DEL_SOURCE="Type DELETE (all caps) to also remove this entire project folder, or press Enter to keep it: "
if "%DEL_SOURCE%"=="DELETE" (
    echo.
    echo Deleting project folder in 5 seconds - close this window now to cancel.
    timeout /t 5 >nul
    set "SELF=%~dp0"
    cd /d "%TEMP%"
    rmdir /s /q "%SELF%"
    echo Project folder removed.
    exit /b 0
) else (
    echo Source code kept. Uninstall finished.
)

pause
exit /b 0

