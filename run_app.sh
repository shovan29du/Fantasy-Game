#!/bin/bash
set -e
cd "$(dirname "$0")"

PYTHON_EXE="python3"
if [ -x ".venv/bin/python" ]; then
  PYTHON_EXE=".venv/bin/python"
fi

if ! command -v "$PYTHON_EXE" >/dev/null 2>&1 && [ ! -x "$PYTHON_EXE" ]; then
  echo "[ERROR] Python 3.10+ not found. Run ./install_unix.sh after installing Python." >&2
  exit 1
fi

echo "Installing required dependencies from requirements.txt ..."
"$PYTHON_EXE" -m pip install -r requirements.txt --quiet

echo "Worldweaver Multiverse Tabletop starting on http://localhost:8501"
echo "Frontend: React. Backend: FastAPI."
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://127.0.0.1:8501" >/dev/null 2>&1 &
elif command -v open >/dev/null 2>&1; then
  open "http://127.0.0.1:8501" >/dev/null 2>&1 &
fi
"$PYTHON_EXE" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8501
