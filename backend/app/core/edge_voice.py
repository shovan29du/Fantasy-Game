"""AiChat Pro — Edge TTS Voice Engine (from RealChar)
Free Microsoft neural TTS. 300+ voices. No API key needed.
pip install edge-tts"""

from core.logging_setup import get_logger

log = get_logger(__name__)
import asyncio, os, tempfile
from typing import List, Dict, Optional

try:
    import edge_tts
    EDGE_TTS_OK = True
except ImportError:
    EDGE_TTS_OK = False

# Popular voices by language/gender
VOICE_PRESETS = {
    "en_male_1": "en-US-ChristopherNeural",
    "en_male_2": "en-US-GuyNeural",
    "en_male_3": "en-GB-RyanNeural",
    "en_female_1": "en-US-JennyNeural",
    "en_female_2": "en-US-AriaNeural",
    "en_female_3": "en-GB-SoniaNeural",
    "en_female_4": "en-US-MichelleNeural",
    "ja_female": "ja-JP-NanamiNeural",
    "ja_male": "ja-JP-KeitaNeural",
    "ko_female": "ko-KR-SunHiNeural",
    "zh_female": "zh-CN-XiaoxiaoNeural",
    "fr_female": "fr-FR-DeniseNeural",
    "de_male": "de-DE-ConradNeural",
    "es_female": "es-ES-ElviraNeural",
    "narrator": "en-US-DavisNeural",
    "anime_girl": "en-US-AnaNeural",
    "deep_male": "en-US-AndrewMultilingualNeural",
}

async def _generate_audio(text: str, voice: str = "en-US-JennyNeural", rate: str = "+0%") -> Optional[bytes]:
    """Generate audio bytes from text using Edge TTS."""
    if not EDGE_TTS_OK: return None
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        audio_data = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
        return bytes(audio_data) if audio_data else None
    except Exception:
        log.debug("suppressed error", exc_info=True)
        return None

def speak_text(text: str, voice: str = "en-US-JennyNeural", rate: str = "+0%") -> Optional[str]:
    """Generate audio file from text. Returns file path or None."""
    if not EDGE_TTS_OK: return None
    clean = text.replace("**","").replace("*","").replace("_","")[:1000]
    try:
        audio = asyncio.run(_generate_audio(clean, voice, rate))
        if audio:
            fd, path = tempfile.mkstemp(suffix=".mp3")
            with os.fdopen(fd, 'wb') as f: f.write(audio)
            return path
    except Exception:
        log.debug("suppressed error", exc_info=True)
        # Try with new event loop
        try:
            loop = asyncio.new_event_loop()
            audio = loop.run_until_complete(_generate_audio(clean, voice, rate))
            loop.close()
            if audio:
                fd, path = tempfile.mkstemp(suffix=".mp3")
                with os.fdopen(fd, 'wb') as f: f.write(audio)
                return path
        except Exception:
            log.debug("suppressed error", exc_info=True)
            pass
    return None

async def list_voices(language: str = "en") -> List[Dict]:
    """List available voices for a language."""
    if not EDGE_TTS_OK: return []
    try:
        voices = await edge_tts.list_voices()
        return [{"name": v["ShortName"], "gender": v["Gender"], "locale": v["Locale"]}
                for v in voices if v["Locale"].startswith(language)]
    except Exception:
        log.debug("suppressed error", exc_info=True)
        return []

def get_voice_for_character(gender: str = "", race: str = "", name: str = "") -> str:
    """Auto-select a voice based on character traits."""
    g = gender.lower() if gender else ""
    if "female" in g or "futa" in g:
        if race and any(w in race.lower() for w in ["elf","fairy","angel"]): return VOICE_PRESETS["anime_girl"]
        return VOICE_PRESETS["en_female_1"]
    elif "male" in g:
        if race and any(w in race.lower() for w in ["orc","dwarf","giant"]): return VOICE_PRESETS["deep_male"]
        return VOICE_PRESETS["en_male_1"]
    return VOICE_PRESETS["narrator"]
