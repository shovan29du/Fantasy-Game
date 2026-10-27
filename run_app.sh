#!/bin/bash
set -e
cd "$(dirname "$0")"

# ── Python detection ──────────────────────────────────────────────────────
PYTHON_EXE="python3"
if [ -x ".venv/bin/python" ]; then
  PYTHON_EXE=".venv/bin/python"
fi

if ! command -v "$PYTHON_EXE" >/dev/null 2>&1 && [ ! -x "$PYTHON_EXE" ]; then
  echo "[ERROR] Python 3.10+ not found. Run ./install_unix.sh after installing Python." >&2
  exit 1
fi

# ── Install / update dependencies ─────────────────────────────────────────
echo "Checking dependencies from requirements.txt ..."
"$PYTHON_EXE" -m pip install -r requirements.txt --quiet

# ── Kill any previous instance on port 8501 ───────────────────────────────
if lsof -ti tcp:8501 >/dev/null 2>&1; then
  echo "Closing previous instance on port 8501 ..."
  lsof -ti tcp:8501 | xargs kill -9 2>/dev/null || true
  sleep 1
fi

# ── Launch ────────────────────────────────────────────────────────────────
echo ""
echo "  ╔══════════════════════════════════════════════════════╗"
echo "  ║   Worldweaver Multiverse Tabletop                    ║"
echo "  ║   http://localhost:8501                              ║"
echo "  ║                                                      ║"
echo "  ║   Start LM Studio on port 1234 for AI chat.         ║"
echo "  ║   Press Ctrl+C to stop the server.                  ║"
echo "  ╚══════════════════════════════════════════════════════╝"
echo ""

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://127.0.0.1:8501" >/dev/null 2>&1 &
elif command -v open >/dev/null 2>&1; then
  open "http://127.0.0.1:8501" >/dev/null 2>&1 &
fi

"$PYTHON_EXE" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8501
