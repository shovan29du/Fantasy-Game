"""Structural validation for the Windows installer package.

These are plain file/content checks (no Windows runtime available in
this environment), so they can't execute the .bat/.ps1 scripts. They
catch the common ways an installer package silently rots: a referenced
file going missing, a stray real secret getting committed, or a
gitignore rule being dropped.
"""
import os
import re

APP_DIR = os.path.dirname(os.path.abspath(__file__))


def _read(name):
    with open(os.path.join(APP_DIR, name), "r", encoding="utf-8") as f:
        return f.read()


def test_installer_files_exist():
    for name in (
        "install_ark_ai.bat",
        "run_ark_ai.bat",
        "upgrade_ark_ai.bat",
        "uninstall_ark_ai.bat",
        "create_shortcuts.ps1",
        "install_ark_ai.command",
        "install_ark_ai.sh",
        "build_release.py",
        "INSTALL_HELP_ALL_OS.txt",
        "ARK_AI_USER_GUIDE.txt",
        "README_INSTALL_WINDOWS.txt",
        ".env.example",
    ):
        assert os.path.isfile(os.path.join(APP_DIR, name)), f"missing {name}"


def test_installer_detects_python_with_fallbacks():
    content = _read("install_ark_ai.bat")
    assert "py -3" in content
    assert "python" in content
    assert "python3" in content


def test_installer_handles_dev_and_postgres_modes():
    content = _read("install_ark_ai.bat")
    assert "requirements-dev.txt" in content
    assert "requirements-postgres.txt" in content
    assert "DATABASE_URL" in content


def test_installer_generates_secret_and_token():
    content = _read("install_ark_ai.bat")
    assert "secrets.token_hex" in content
    assert "ARK_AI_SECRET_KEY" in content
    assert "ARK_AI_TOKEN" in content


def test_installer_initializes_database():
    content = _read("install_ark_ai.bat")
    assert "db.init_db()" in content


def test_installer_calls_shortcut_script():
    content = _read("install_ark_ai.bat")
    assert "create_shortcuts.ps1" in content


def test_launcher_loads_env_and_activates_venv():
    content = _read("run_ark_ai.bat")
    assert "venv\\Scripts\\python.exe" in content
    assert ".env" in content
    assert "Virtual environment not found - setting it up now." in content
    assert "-m venv venv" in content
    assert "pip install -r requirements.txt" in content
    assert "db.init_db()" in content
    assert "pause" in content  # window stays open so crashes are readable


def test_simple_launcher_bootstraps_first_run():
    content = _read("run.bat")
    assert "-m venv venv" in content
    assert "pip install -r requirements.txt" in content
    assert "db.init_db()" in content


def test_upgrade_helper_preserves_user_data():
    content = _read("upgrade_ark_ai.bat")
    for name in (".env", "config.json", "ark_ai.db", "realzip.db", "workspace", "venv"):
        assert name in content
    assert "_upgrade_backup_" in content
    assert "db.init_db()" in content


def test_uninstaller_asks_before_destructive_actions():
    content = _read("uninstall_ark_ai.bat")
    assert "Delete the virtual environment" in content
    assert "Delete local SQLite database" in content
    assert "DELETE" in content  # explicit typed confirmation to remove source


def test_uninstaller_does_not_unconditionally_remove_source():
    content = _read("uninstall_ark_ai.bat")
    # The only rmdir of the project root must be gated behind the typed
    # "DELETE" confirmation, not a plain y/n prompt.
    assert 'if "%DEL_SOURCE%"=="DELETE"' in content


def test_shortcut_script_targets_launcher_and_prefers_onedrive():
    content = _read("create_shortcuts.ps1")
    assert "run_ark_ai.bat" in content
    assert "$env:OneDrive" in content
    assert "$desktopTargets.Contains($normalDesktop)" in content
    assert "Start Menu\\Programs" in content
    assert "Ark_AI.lnk" in content


def test_python_installer_targets_both_desktops():
    content = _read("full_install.py")
    assert "onedrive_desktop_roots()" in content
    assert "normal_desktop()" in content
    assert "if normal not in targets" in content


def test_macos_installer_uses_cross_platform_python_installer():
    content = _read("install_ark_ai.command")
    assert content.startswith("#!/bin/bash")
    assert "python3" in content
    assert "full_install.py" in content
    assert "Ark_Ai.command" in content


def test_linux_installer_uses_cross_platform_python_installer():
    content = _read("install_ark_ai.sh")
    assert content.startswith("#!/usr/bin/env bash")
    assert "set -euo pipefail" in content
    assert "python3" in content
    assert "full_install.py" in content
    assert "./run.sh" in content


def test_linux_desktop_entry_quotes_paths_with_spaces():
    content = _read("full_install.py")
    assert 'Exec=\\"{target}\\" \\"{script}\\"' in content


def test_release_builder_preserves_macos_executable_mode():
    content = _read("build_release.py")
    assert 'EXECUTABLE_SUFFIXES = {".command", ".sh"}' in content
    assert "0o755" in content
    assert "info.external_attr" in content


def test_cross_platform_help_covers_every_installer():
    content = _read("INSTALL_HELP_ALL_OS.txt")
    for name in ("install_ark_ai.bat", "install_ark_ai.command", "install_ark_ai.sh", "full_install.py"):
        assert name in content


def test_user_guide_covers_major_features():
    content = _read("ARK_AI_USER_GUIDE.txt")
    for feature in ("CHAT MODES", "DOCUMENTS AND URL READING", "MEMORY", "VOICE AND ACCESSIBILITY",
                    "AGENTS AND INSTALLED SKILLS", "SLASH COMMANDS", "PRIVACY AND SECURITY"):
        assert feature in content


def test_env_example_has_no_real_secret_value():
    content = _read(".env.example")
    for line in content.splitlines():
        if line.strip().startswith("ARK_AI_SECRET_KEY=") or line.strip().startswith("ARK_AI_TOKEN="):
            value = line.split("=", 1)[1].strip()
            assert value == "", f"committed template must not contain a real secret: {line!r}"


def test_gitignore_excludes_local_config_and_db():
    content = _read(".gitignore")
    for pattern in (".env", "venv/", "*.db", "config.json"):
        assert pattern in content


def test_no_real_database_url_with_credentials_committed():
    """Catches accidentally committing a real DATABASE_URL with embedded
    credentials in any installer/doc/template file."""
    leak_re = re.compile(r"postgresql://[^/\s]+:[^/\s@]+@")
    for name in ("install_ark_ai.bat", ".env.example", "README_INSTALL_WINDOWS.txt"):
        content = _read(name)
        for match in leak_re.finditer(content):
            assert match.group(0) in (
                "postgresql://user:pass@",
            ), f"looks like a real credential in {name}: {match.group(0)!r}"
