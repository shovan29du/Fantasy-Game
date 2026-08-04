"""Compatibility package for backend\app\story."""
from pathlib import Path

_target = Path(__file__).resolve().parent.parent / "backend" / "app" / "story"
__path__ = [str(_target), *__path__]
