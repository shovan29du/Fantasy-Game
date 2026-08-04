"""Compatibility package for backend.app.core."""
from pathlib import Path

_backend_core = Path(__file__).resolve().parent.parent / "backend" / "app" / "core"
__path__ = [str(_backend_core), *__path__]
