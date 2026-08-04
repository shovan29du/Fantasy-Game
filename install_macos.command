#!/bin/bash
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] Python 3.10+ is required to install Worldweaver." >&2
  exit 1
fi

case "${1:-}" in
  all)
    python3 full_install.py --all-optional
    ;;
  minimal)
    python3 full_install.py --minimal
    ;;
  *)
    python3 full_install.py
    ;;
esac
