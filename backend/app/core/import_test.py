"""AiChat Pro v21 â€” Import Test Runner
Automated script that tests every import path end-to-end.
Run standalone: python -m core.import_test
Or call run_all() from app startup."""
import importlib
import traceback
from typing import List, Tuple

CORE_MODULES = [
    "core.storage",
    "core.db_migration",
    "core.chat_engine",
    "core.character_data",
    "core.levelling",
    "core.relationship_engine",
    "core.quest_system",
    "core.memory_engine",
    "core.image_gen",
    "core.world_engine",
    "core.knowledge_base",
    "core.auto_fill",
    "core.safety",
    "core.security",
    "core.safe_ui",
    "core.voice_system",
    "core.planning",
    "core.model_manager",
    "core.plugin_manager",
    "core.backup_restore",
    "core.simulation_engine",
    "core.media_pipeline",
    "core.character_search",
    "core.web_search",
]

UI_MODULES = [
    "backend.app.main",
    "backend.app.services.chat_service",
    "backend.app.services.character_service",
    "backend.app.services.scenario_template_service",
]

def test_imports(modules: List[str] = None) -> Tuple[List[str], List[Tuple[str, str]]]:
    """Test importing modules. Returns (passed, failed) where failed is list of (module, error)."""
    if modules is None:
        modules = CORE_MODULES + UI_MODULES
    passed = []
    failed = []
    for mod in modules:
        try:
            importlib.import_module(mod)
            passed.append(mod)
        except Exception as e:
            failed.append((mod, f"{type(e).__name__}: {e}"))
    return passed, failed

def run_all(verbose: bool = True) -> bool:
    """Run full import test. Returns True if all pass."""
    passed, failed = test_imports(CORE_MODULES)
    if verbose:
        for m in passed:
            print(f"  âœ… {m}")
        for m, e in failed:
            print(f"  âŒ {m} â†’ {e}")
    return len(failed) == 0

if __name__ == "__main__":
    print("AiChat Pro â€” Import Test Runner")
    print("=" * 50)
    print("\nðŸ”§ Core Modules:")
    p1, f1 = test_imports(CORE_MODULES)
    for m in p1: print(f"  âœ… {m}")
    for m, e in f1: print(f"  âŒ {m} â†’ {e}")
    print(f"\nðŸ–¼ï¸ App Modules:")
    p2, f2 = test_imports(UI_MODULES)
    for m in p2: print(f"  âœ… {m}")
    for m, e in f2: print(f"  âŒ {m} â†’ {e}")
    total = len(p1) + len(p2) + len(f1) + len(f2)
    fails = len(f1) + len(f2)
    print(f"\n{'âœ…' if fails == 0 else 'âŒ'} {total - fails}/{total} passed")


