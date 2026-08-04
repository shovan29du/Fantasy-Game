"""AiChat Pro — Edge TTS Engine (from RealChar)
Free, high-quality Microsoft Edge text-to-speech.
No API key needed. 300+ voices. Multiple languages.
pip install edge-tts"""

from core.logging_setup import get_logger

log = get_logger(__name__)
import asyncio, os, tempfile
from typing import List, Dict, Optional

# Available voice presets by character type
VOICE_PRESETS = {
    "male_neutral": "en-US-GuyNeural",
    "male_deep": "en-US-ChristopherNeural",
    "male_young": "en-US-EricNeural",
    "female_neutral": "en-US-JennyNeural",
    "female_warm": "en-US-AriaNeural",
    "female_young": "en-US-MichelleNeural",
    "male_british": "en-GB-RyanNeural",
    "female_british": "en-GB-SoniaNeural",
    "male_australian": "en-AU-WilliamNeural",
    "female_japanese": "ja-JP-NanamiNeural",
    "male_japanese": "ja-JP-KeitaNeural",
    "female_korean": "ko-KR-SunHiNeural",
    "narrator": "en-US-ChristopherNeural",
    "villain": "en-US-GuyNeural",
    "child": "en-US-AnaNeural",
}

async def _generate_edge_tts(text: str, voice: str = "en-US-ChristopherNeural",
                              rate: str = "+0%") -> Optional[str]:
    """Generate audio file using Edge TTS. Returns temp file path."""
    try:
        from edge_tts import Communicate
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            outpath = f.name
        communicate = Communicate(text, voice, rate=rate)
        await communicate.save(outpath)
        return outpath
    except ImportError:
        return None
    except Exception:
        return None

def speak_edge_tts(text: str, voice: str = "en-US-ChristopherNeural",
                    rate: str = "+0%") -> Optional[str]:
    """Synchronous wrapper for Edge TTS. Returns file path or None."""
    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_generate_edge_tts(text, voice, rate))
        loop.close()
        return result
    except Exception:
        return None

async def get_available_voices(language: str = "en") -> List[Dict]:
    """Get available voices for a language."""
    try:
        from edge_tts import VoicesManager
        voices = await VoicesManager.create()
        matching = voices.find(Language=language)
        return [{"name": v["ShortName"], "gender": v["Gender"], "locale": v["Locale"]}
                for v in matching]
    except Exception:
        log.debug("suppressed error", exc_info=True)
        return []

def get_voice_for_character(gender: str = "", race: str = "") -> str:
    """Auto-select voice based on character traits."""
    g = gender.lower() if gender else ""
    if "female" in g or "woman" in g:
        if "japan" in (race or "").lower(): return VOICE_PRESETS["female_japanese"]
        if "brit" in (race or "").lower() or "elf" in (race or "").lower(): return VOICE_PRESETS["female_british"]
        return VOICE_PRESETS["female_warm"]
    elif "male" in g or "man" in g:
        if "japan" in (race or "").lower(): return VOICE_PRESETS["male_japanese"]
        if "brit" in (race or "").lower() or "elf" in (race or "").lower(): return VOICE_PRESETS["male_british"]
        return VOICE_PRESETS["male_deep"]
    return VOICE_PRESETS["narrator"]
