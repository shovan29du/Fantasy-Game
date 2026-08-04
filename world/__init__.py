"""Compatibility package for backend\app\world."""
from pathlib import Path

_target = Path(__file__).resolve().parent.parent / "backend" / "app" / "world"
__path__ = [str(_target), *__path__]
