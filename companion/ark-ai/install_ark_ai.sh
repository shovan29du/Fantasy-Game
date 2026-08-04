#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "  Ark_Ai - Linux Installer"
echo "============================================================"
echo "Installing into: $SCRIPT_DIR"
echo

if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "ERROR: Python 3.10 or newer is required."
  echo "Install it with your distribution's package manager, then run this installer again."
  exit 1
fi

"$PYTHON" full_install.py

echo
echo "Installation complete."
echo "Start ARK AI with ./run.sh or the Ark_Ai desktop launcher."
