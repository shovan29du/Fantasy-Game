"""AiChat Pro — Shared Configuration

Resolution order for provider URLs and other tunables (highest priority first):
  1. Environment variable
  2. config/local.json (optional, gitignored — copy config/local.json.example)
  3. Built-in safe default (always localhost/127.0.0.1, never a remote host)

Nothing here talks to the network or requires internet access. All defaults
point at services expected to run on the same machine.
"""
from pathlib import Path
import json
import os

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MEDIA_DIR = BASE_DIR / "media"
IMAGE_DIR = MEDIA_DIR / "images"
LOG_DIR = BASE_DIR / "logs"
BACKUP_DIR = BASE_DIR / "backups"
PLUGIN_DIR = BASE_DIR / "plugins"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
VOICE_DIR = BASE_DIR / "voices"
CONFIG_DIR = BASE_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "local.json"

for d in [DATA_DIR, MEDIA_DIR, IMAGE_DIR, LOG_DIR, BACKUP_DIR, PLUGIN_DIR, KNOWLEDGE_DIR, VOICE_DIR, CONFIG_DIR,
          MEDIA_DIR / "picture", MEDIA_DIR / "video", MEDIA_DIR / "animation"]:
    d.mkdir(parents=True, exist_ok=True)


def _load_config_file() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        # Config file is optional and user-edited; a parse error must not
        # block startup. core.logging_setup isn't guaranteed to be importable
        # yet at this point in the import graph, so fall back to stderr.
        import sys
        print(f"[shared_config] Warning: could not parse {CONFIG_FILE}, ignoring it.", file=sys.stderr)
        return {}


_FILE_CONFIG = _load_config_file()


def get_setting(key: str, default: str) -> str:
    """Resolve a setting: env var > config/local.json > default."""
    if key in os.environ:
        return os.environ[key]
    if key in _FILE_CONFIG:
        return str(_FILE_CONFIG[key])
    return default


APP_TITLE = "AiChat Pro"
APP_VERSION = "74.5.0"

# ═══ Optional local provider integrations — all default to localhost ═══
LM_STUDIO_URL = get_setting("LM_STUDIO_URL", "http://127.0.0.1:1234/v1")
LM_STUDIO_MODEL = get_setting("LM_STUDIO_MODEL", "local-model")
COMFYUI_URL = get_setting("COMFYUI_URL", "http://127.0.0.1:8188")
A1111_URL = get_setting("A1111_URL", "http://127.0.0.1:7860")

DEFAULT_CONTEXT_LIMIT = 15
MAX_LIBRARY_DISPLAY = 50
AUTO_LOCK_SECONDS = 300
