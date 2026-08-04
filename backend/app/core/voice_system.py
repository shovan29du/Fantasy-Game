"""
AiChat Pro — Voice System
Whisper speech-to-text, Piper text-to-speech, wake-word placeholder.
"""
from __future__ import annotations
import subprocess
import logging
import os
from pathlib import Path
from shared_config import VOICE_DIR

logger = logging.getLogger(__name__)


class VoiceSystem:
    def __init__(self):
        self._whisper_model = None

    # ── Whisper STT ─────────────────────────────────────────
    def load_whisper(self, model_size: str = "base"):
        try:
            import whisper
            self._whisper_model = whisper.load_model(model_size)
            logger.info("Whisper model loaded: %s", model_size)
        except Exception as e:
            logger.error("Whisper load failed: %s", e)

    def transcribe(self, audio_path: str) -> str:
        if not self._whisper_model:
            self.load_whisper()
        if not self._whisper_model:
            return "[Whisper not available]"
        try:
            result = self._whisper_model.transcribe(audio_path)
            return result.get("text", "")
        except Exception as e:
            return f"[Transcription error] {e}"

    # ── Piper TTS ───────────────────────────────────────────
    def speak(self, text: str, voice_model: str = "en_US-lessac-medium.onnx",
              output_path: str = None) -> str:
        output_path = output_path or str(VOICE_DIR / "speech_output.wav")
        model_path = str(VOICE_DIR / voice_model)
        if not Path(model_path).exists():
            model_path = voice_model  # try system path
        try:
            proc = subprocess.run(
                ["piper", "--model", model_path, "--output_file", output_path],
                input=text.encode(), capture_output=True, timeout=30)
            if proc.returncode == 0:
                return output_path
        except FileNotFoundError:
            logger.warning("Piper not found in PATH")
        except Exception as e:
            logger.error("TTS error: %s", e)
        return ""

    # ── Wake word (placeholder) ─────────────────────────────
    def check_wake_word_available(self) -> bool:
        try:
            import pvporcupine
            return True
        except ImportError:
            return False


# Singleton
voice_system = VoiceSystem()
