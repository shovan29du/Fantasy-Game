"""
AiChat Pro — Model Manager
Register, switch, and monitor local LLM models via LM Studio.
"""
from __future__ import annotations
import logging
from typing import List, Dict, Optional
from shared_config import LM_STUDIO_URL

logger = logging.getLogger(__name__)

try:
    import requests as _req
except ImportError:
    _req = None


class ModelManager:
    def __init__(self):
        self.active_model: Optional[str] = None
        self.registered: Dict[str, str] = {}

    def register(self, name: str, model_id: str):
        self.registered[name] = model_id

    def switch(self, name: str) -> bool:
        if name in self.registered:
            self.active_model = name
            logger.info("Switched to model: %s", name)
            return True
        return False

    def list_models(self) -> List[str]:
        return list(self.registered.keys())

    def detect_lm_studio_models(self) -> List[str]:
        if not _req:
            return []
        try:
            r = _req.get(f"{LM_STUDIO_URL}/models", timeout=5)
            if r.status_code == 200:
                data = r.json()
                return [m.get("id", "unknown") for m in data.get("data", [])]
        except Exception:
            pass
        return []

    def is_lm_studio_running(self) -> bool:
        if not _req:
            return False
        try:
            r = _req.get(f"{LM_STUDIO_URL}/models", timeout=3)
            return r.status_code == 200
        except Exception:
            return False


model_manager = ModelManager()
