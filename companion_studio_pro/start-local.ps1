$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root
$python = Get-Command python -ErrorAction SilentlyContinue
if (!$python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (!$python) { throw "Python 3.11 or newer is required. Install Python, then run this file again." }
if (!(Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
  & $python.Source -m venv .venv
  & ".venv\Scripts\python.exe" -m pip install -r "local_api\requirements.txt"
}
Start-Process -FilePath (Resolve-Path ".venv\Scripts\python.exe") -ArgumentList @("-m","uvicorn","local_api.main:app","--host","127.0.0.1","--port","8765") -WorkingDirectory $root -WindowStyle Hidden
npm.cmd install
npm.cmd run dev
