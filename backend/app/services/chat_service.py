"""Chat service boundary for UI and future HTTP API callers."""
from core.chat_engine import build_system_prompt, get_history, save_message, stream_from_llm

__all__ = ["build_system_prompt", "get_history", "save_message", "stream_from_llm"]
