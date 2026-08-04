@echo off
setlocal EnableExtensions
title Ark_AI installer
cd /d "%~dp0"

echo.
echo   ===========================================
echo     Ark_AI - personal AI workspace
echo   ===========================================
echo.

REM --- locate Python ---
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY ( where python >nul 2>&1 && set "PY=python" )
if not defined PY (
  echo   Python 3 was not found on this PC.
  echo   Opening the download page - install it, tick
  echo   "Add python.exe to PATH", then run install.bat again.
  start "" "https://www.python.org/downloads/"
  echo.
  pause
  exit /b 1
)
echo   Using Python: %PY%

REM --- virtual environment ---
if not exist "venv\Scripts\python.exe" (
  echo   Creating virtual environment...
  %PY% -m venv venv
  if errorlevel 1 ( echo   ERROR: could not create venv. & pause & exit /b 1 )
)

echo   Installing dependencies (Flask, requests)...
"venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 ( echo   ERROR: dependency install failed. & pause & exit /b 1 )

REM --- desktop shortcut (auto-detects OneDrive Desktop) ---
echo   Creating desktop shortcut...
set "APPDIR=%~dp0"
if "%APPDIR:~-1%"=="\" set "APPDIR=%APPDIR:~0,-1%"
set "RELAY_APPDIR=%APPDIR%"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$a=$env:RELAY_APPDIR;" ^
  "$d=[Environment]::GetFolderPath('Desktop');" ^
  "foreach($root in @($env:OneDriveCommercial,$env:OneDrive)){ if($root){ $c=Join-Path $root 'Desktop'; if(Test-Path $c){ $d=$c; break } } }" ^
  "if(-not (Test-Path $d)){ New-Item -ItemType Directory -Force -Path $d ^| Out-Null }" ^
  "$q=[char]34;" ^
  "$w=New-Object -ComObject WScript.Shell;" ^
  "$s=$w.CreateShortcut((Join-Path $d 'Ark_AI.lnk'));" ^
  "$s.TargetPath=(Join-Path $a 'venv\Scripts\pythonw.exe');" ^
  "$s.Arguments=$q+(Join-Path $a 'app.py')+$q;" ^
  "$s.WorkingDirectory=$a;" ^
  "$s.IconLocation=(Join-Path $a 'relay.ico');" ^
  "$s.Description='Ark_AI - personal AI workspace';" ^
  "$s.Save();" ^
  "Write-Host ('   Shortcut placed in: ' + $d)"

echo.
echo   Setup complete. Launching Ark_AI...
start "" "%APPDIR%\venv\Scripts\pythonw.exe" "%APPDIR%\app.py"
echo   A browser tab will open at http://127.0.0.1:5000
echo   (Add your free OpenRouter key in Settings to begin.)
echo.
timeout /t 3 >nul
exit /b 0
