"""Compatibility package for backend\app\chat_io."""
from pathlib import Path

_target = Path(__file__).resolve().parent.parent / "backend" / "app" / "chat_io"
__path__ = [str(_target), *__path__]
