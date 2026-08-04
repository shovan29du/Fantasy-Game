"""AiChat Pro — Lightweight logging setup.

Configures a rotating file handler under logs/aichat_pro.log plus console
output. Call configure_logging() once at app startup; use get_logger(__name__)
everywhere else.
"""
from __future__ import annotations
import logging
import logging.handlers
import os
from pathlib import Path

_CONFIGURED = False


def configure_logging(log_dir: Path | str | None = None, level: int | None = None) -> None:
    """Idempotent logging configuration for the whole app."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    if log_dir is None:
        from shared_config import LOG_DIR
        log_dir = LOG_DIR
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    if level is None:
        level = getattr(logging, os.environ.get("AICHAT_LOG_LEVEL", "INFO").upper(), logging.INFO)

    root = logging.getLogger("aichat_pro")
    root.setLevel(level)
    root.propagate = False

    if root.handlers:
        _CONFIGURED = True
        return

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "aichat_pro.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    root.addHandler(console_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger namespaced under 'aichat_pro'. Configures logging on first use."""
    if not _CONFIGURED:
        configure_logging()
    if not name.startswith("aichat_pro"):
        name = f"aichat_pro.{name}"
    return logging.getLogger(name)
