"""Plugin discovery, loading, and hook execution (core/plugin_manager.py)."""
from core.plugin_manager import PluginManager


def _write_plugin(plugin_dir, name, body):
    (plugin_dir / f"{name}.py").write_text(body, encoding="utf-8")


def test_discover_finds_py_files_and_skips_private(tmp_path, monkeypatch):
    import core.plugin_manager as pm
    monkeypatch.setattr(pm, "PLUGIN_DIR", tmp_path)
    _write_plugin(tmp_path, "greeter", "def on_user_message(data): pass")
    _write_plugin(tmp_path, "_private", "x = 1")
    (tmp_path / "notes.txt").write_text("not a plugin")

    manager = PluginManager()
    found = manager.discover()
    assert found == ["greeter"]


def test_load_and_run_hook_calls_plugin_function(tmp_path, monkeypatch):
    import core.plugin_manager as pm
    monkeypatch.setattr(pm, "PLUGIN_DIR", tmp_path)
    calls_path = tmp_path / "calls.txt"
    _write_plugin(tmp_path, "logger_plugin", f"""
def on_user_message(data):
    with open(r"{calls_path}", "a") as f:
        f.write(data.get("content", "") + "\\n")
""")
    manager = PluginManager()
    assert manager.load("logger_plugin") is True
    manager.run_hook("on_user_message", {"content": "hello world"})
    assert calls_path.read_text().strip() == "hello world"


def test_disabled_plugin_does_not_run(tmp_path, monkeypatch):
    import core.plugin_manager as pm
    monkeypatch.setattr(pm, "PLUGIN_DIR", tmp_path)
    calls_path = tmp_path / "calls.txt"
    _write_plugin(tmp_path, "quiet_plugin", f"""
def on_user_message(data):
    with open(r"{calls_path}", "a") as f:
        f.write("called\\n")
""")
    manager = PluginManager()
    manager.load("quiet_plugin")
    manager.toggle("quiet_plugin", False)
    manager.run_hook("on_user_message", {"content": "hi"})
    assert not calls_path.exists()


def test_run_hook_survives_a_broken_plugin(tmp_path, monkeypatch):
    import core.plugin_manager as pm
    monkeypatch.setattr(pm, "PLUGIN_DIR", tmp_path)
    _write_plugin(tmp_path, "broken", "def on_user_message(data): raise ValueError('boom')")
    manager = PluginManager()
    manager.load("broken")
    # Must not raise -- a broken plugin should never take down the chat flow.
    manager.run_hook("on_user_message", {"content": "hi"})


def test_load_missing_plugin_returns_false(tmp_path, monkeypatch):
    import core.plugin_manager as pm
    monkeypatch.setattr(pm, "PLUGIN_DIR", tmp_path)
    manager = PluginManager()
    assert manager.load("does_not_exist") is False
