"""Smoke test: every core/UI module must import cleanly."""
from core.import_test import CORE_MODULES, UI_MODULES
from core.import_test import test_imports as _run_import_check


def test_core_modules_import():
    passed, failed = _run_import_check(CORE_MODULES)
    assert not failed, f"Core module import failures: {failed}"
    assert set(passed) == set(CORE_MODULES)


def test_ui_modules_import():
    passed, failed = _run_import_check(UI_MODULES)
    assert not failed, f"UI module import failures: {failed}"
    assert set(passed) == set(UI_MODULES)
