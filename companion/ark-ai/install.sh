#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
echo "  Ark_AI - personal AI workspace"
PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then echo "  Python 3 not found. Install it from https://www.python.org/downloads/"; exit 1; fi
echo "  Using $($PY --version)"
[ -d venv ] || { echo "  Creating virtual environment..."; "$PY" -m venv venv; }
echo "  Installing dependencies..."
./venv/bin/python -m pip install --upgrade pip >/dev/null
./venv/bin/python -m pip install -r requirements.txt
chmod +x run.sh 2>/dev/null || true
# Linux desktop launcher
DESK="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
if [ -d "$DESK" ] && [ "$(uname)" = "Linux" ]; then
  cat > "$DESK/Ark_AI.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Ark_AI
Comment=Personal AI workspace
Exec=$(pwd)/run.sh
Icon=$(pwd)/relay.png
Terminal=false
Categories=Utility;
DESKTOP
  chmod +x "$DESK/Ark_AI.desktop" 2>/dev/null || true
  echo "  Desktop launcher created at $DESK/Ark_AI.desktop"
fi
echo "  Done. Start it with:  ./run.sh"
