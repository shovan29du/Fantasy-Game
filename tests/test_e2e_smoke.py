"""Browser smoke test: start a game, chat, use the dialogs, fight, return to the hub.

Runs the real server against a throwaway database and a fake LM Studio, then
drives it with Playwright (tests/e2e/smoke.js). Skipped when Node or
Playwright is not installed.
"""
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
E2E = ROOT / "tests" / "e2e"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for(url: str, timeout: float = 30) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2).close()
            return
        except Exception:
            time.sleep(0.3)
    raise RuntimeError(f"{url} did not come up")


def _playwright_available() -> bool:
    node = shutil.which("node")
    if not node:
        return False
    probe = subprocess.run([node, "-e", "require('playwright')"], capture_output=True, cwd=E2E)
    return probe.returncode == 0


@pytest.mark.skipif(not _playwright_available(), reason="Node with Playwright is not installed")
def test_browser_smoke(tmp_path):
    lm_port, app_port = _free_port(), _free_port()
    env = {
        **os.environ,
        "AICHAT_DB_PATH": str(tmp_path / "e2e.db"),
        "LM_STUDIO_URL": f"http://127.0.0.1:{lm_port}/v1",
    }
    # Keep the run offline: no external image provider.
    subprocess.run(
        [sys.executable, "-c",
         "import core.storage as s; s.init_db(); s.set_setting('local_only_mode', '1')"],
        cwd=ROOT, env=env, check=True,
    )
    procs = [
        subprocess.Popen([sys.executable, str(E2E / "fake_lm_studio.py"), str(lm_port)]),
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", str(app_port)],
            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ),
    ]
    try:
        _wait_for(f"http://127.0.0.1:{lm_port}/v1/models")
        _wait_for(f"http://127.0.0.1:{app_port}/")
        result = subprocess.run(
            ["node", str(E2E / "smoke.js")],
            env={**env, "APP_URL": f"http://127.0.0.1:{app_port}", "LM_URL": f"http://127.0.0.1:{lm_port}"},
            capture_output=True, text=True, timeout=240, cwd=E2E,
        )
        assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-2000:]
    finally:
        for proc in procs:
            proc.terminate()
        for proc in procs:
            proc.wait(timeout=10)
