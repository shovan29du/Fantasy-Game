"""
AiChat Pro — Plugin Manager
Discover, load, enable/disable Python plugins from /plugins/ folder.
Each plugin may define on_user_message(data) and on_ai_response(data) hooks.
"""
from __future__ import annotations
import importlib.util
import logging
import os
from typing import Dict, Any, List
from shared_config import PLUGIN_DIR

logger = logging.getLogger(__name__)


class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, Any] = {}
        self.enabled: Dict[str, bool] = {}

    def discover(self) -> List[str]:
        found = []
        for f in os.listdir(PLUGIN_DIR):
            if f.endswith(".py") and not f.startswith("_"):
                found.append(f[:-3])
        return found

    def load(self, name: str) -> bool:
        path = os.path.join(PLUGIN_DIR, f"{name}.py")
        if not os.path.exists(path):
            return False
        try:
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self.plugins[name] = mod
            self.enabled[name] = True
            logger.info("Loaded plugin: %s", name)
            return True
        except Exception as e:
            logger.error("Plugin load error (%s): %s", name, e)
            return False

    def load_all(self):
        for name in self.discover():
            self.load(name)

    def toggle(self, name: str, state: bool):
        self.enabled[name] = state

    def run_hook(self, hook: str, data: Any):
        for name, mod in self.plugins.items():
            if not self.enabled.get(name, False):
                continue
            fn = getattr(mod, hook, None)
            if fn:
                try:
                    fn(data)
                except Exception as e:
                    logger.error("Plugin hook error (%s.%s): %s", name, hook, e)

    def list_plugins(self) -> List[Dict]:
        return [{"name": n, "enabled": self.enabled.get(n, False)}
                for n in self.plugins]


plugin_manager = PluginManager()

_loaded = False


def ensure_loaded() -> None:
    """Discover and load every plugin in plugins/ exactly once per process."""
    global _loaded
    if not _loaded:
        plugin_manager.load_all()
        _loaded = True
