#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "  Ark_Ai - macOS Installer"
echo "============================================================"
echo "Installing into: $SCRIPT_DIR"
echo

if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "ERROR: Python 3 was not found."
  echo "Install Python 3.10 or newer from https://www.python.org/downloads/macos/"
  read -r -p "Press Return to close..."
  exit 1
fi

"$PYTHON" full_install.py

echo
echo "Installation complete."
echo "Use the Ark_Ai.command shortcut on your Desktop to start ARK AI."
read -r -p "Press Return to close..."
