"""Compatibility package for backend\app\map_engine."""
from pathlib import Path

_target = Path(__file__).resolve().parent.parent / "backend" / "app" / "map_engine"
__path__ = [str(_target), *__path__]
