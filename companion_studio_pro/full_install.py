#!/usr/bin/env python3
"""Complete cross-platform installer for Companion Studio Pro."""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG = ROOT / "install.log"
CATALOG = ROOT / "optional_engines/catalog.json"
IS_WIN = os.name == "nt"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")
WARNINGS: list[str] = []


def log(message: str):
    print(message, flush=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def run(command: list[str], *, env=None):
    log("  -> " + " ".join(command[:4]) + (" ..." if len(command) > 4 else ""))
    with LOG.open("a", encoding="utf-8") as handle:
        return subprocess.run(command, cwd=ROOT, env=env, stdout=handle,
                              stderr=subprocess.STDOUT, check=True)


def executable(name: str):
    return shutil.which(name)


def optional_step(name, callback):
    try:
        callback()
        log(f"  [ok] {name}")
        return True
    except Exception as exc:
        warning = f"{name}: {exc}"
        WARNINGS.append(warning)
        log(f"  [warning] {warning}")
        return False


def ensure_python():
    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11 or newer is required.")


def ensure_node():
    npm = executable("npm.cmd" if IS_WIN else "npm")
    if executable("node") and npm:
        return npm
    if IS_WIN and executable("winget"):
        run(["winget", "install", "--id", "OpenJS.NodeJS.LTS", "-e",
             "--accept-package-agreements", "--accept-source-agreements"])
    elif IS_MAC and executable("brew"):
        run(["brew", "install", "node"])
    elif IS_LINUX and executable("apt-get"):
        run(["sudo", "apt-get", "update"])
        run(["sudo", "apt-get", "install", "-y", "nodejs", "npm", "git"])
    elif IS_LINUX and executable("dnf"):
        run(["sudo", "dnf", "install", "-y", "nodejs", "npm", "git"])
    else:
        raise SystemExit("Install Node.js 22+ and Git, then run this installer again.")
    npm = executable("npm.cmd" if IS_WIN else "npm")
    if not npm:
        raise SystemExit("Node installed; reopen the terminal and run this installer again.")
    return npm


def venv_python(folder=".venv"):
    return ROOT / folder / ("Scripts/python.exe" if IS_WIN else "bin/python")


def install_core(npm: str):
    log("\n[1/7] Installing the editor and local API")
    py = venv_python()
    if not py.exists():
        run([sys.executable, "-m", "venv", str(ROOT / ".venv")])
    run([str(py), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    run([str(py), "-m", "pip", "install", "-r", str(ROOT / "local_api/requirements.txt")])
    log("\n[2/7] Installing the interface and bundled FFmpeg")
    run([npm, "install", "--no-audit", "--no-fund"])
    run([npm, "run", "build"])


def nvidia_present():
    return bool(executable("nvidia-smi"))


def install_gpu():
    log("\n[3/7] Installing image, speech, caption, and GPU libraries")
    py = str(venv_python())
    torch = [py, "-m", "pip", "install", "torch", "torchvision", "torchaudio"]
    if nvidia_present() and not IS_MAC:
        torch += ["--index-url", "https://download.pytorch.org/whl/cu128"]
    run(torch)
    run([py, "-m", "pip", "install", "-r",
         str(ROOT / "optional_engines/requirements-gpu.txt")])


def install_ollama(pull_model=True):
    log("\n[4/7] Installing Ollama")
    ollama = executable("ollama.exe" if IS_WIN else "ollama")
    if not ollama:
        if IS_WIN and executable("winget"):
            run(["winget", "install", "--id", "Ollama.Ollama", "-e",
                 "--accept-package-agreements", "--accept-source-agreements"])
        elif IS_MAC and executable("brew"):
            run(["brew", "install", "--cask", "ollama"])
        elif IS_LINUX:
            with tempfile.TemporaryDirectory() as folder:
                script = Path(folder) / "ollama-install.sh"
                urllib.request.urlretrieve("https://ollama.com/install.sh", script)
                run(["sh", str(script)])
        else:
            raise RuntimeError("No supported Ollama package manager found")
        ollama = executable("ollama.exe" if IS_WIN else "ollama")
    if not ollama and IS_WIN:
        candidate = Path(os.getenv("LOCALAPPDATA", "")) / "Programs/Ollama/ollama.exe"
        ollama = str(candidate) if candidate.exists() else None
    if not ollama:
        raise RuntimeError("installed but PATH needs a terminal restart")
    if pull_model:
        run([str(ollama), "pull", "qwen2.5:3b"])
        # Vision model reads text, charts, tables, diagrams and formulas from video frames.
        run([str(ollama), "pull", "qwen2.5vl:3b"])


def install_ocr():
    """Install the native OCR executable used by pytesseract."""
    log("\n[4/7] Installing the local OCR engine")
    if executable("tesseract"):
        return
    if IS_WIN and executable("winget"):
        run(["winget", "install", "--id", "UB-Mannheim.TesseractOCR", "-e",
             "--accept-package-agreements", "--accept-source-agreements"])
    elif IS_MAC and executable("brew"):
        run(["brew", "install", "tesseract"])
    elif IS_LINUX and executable("apt-get"):
        run(["sudo", "apt-get", "install", "-y", "tesseract-ocr"])
    elif IS_LINUX and executable("dnf"):
        run(["sudo", "dnf", "install", "-y", "tesseract"])
    else:
        raise RuntimeError("No supported Tesseract package installer found")


def install_comfyui():
    log("\n[5/7] Installing ComfyUI in its own environment")
    git = executable("git")
    if not git:
        raise RuntimeError("Git is required")
    source = ROOT / "engines/ComfyUI"
    envdir = ROOT / "engines/comfyui-venv"
    source.parent.mkdir(exist_ok=True)
    if not source.exists():
        run([git, "clone", "--depth", "1",
             "https://github.com/comfyanonymous/ComfyUI.git", str(source)])
    py = venv_python("engines/comfyui-venv")
    if not py.exists():
        run([sys.executable, "-m", "venv", str(envdir)])
    run([str(py), "-m", "pip", "install", "--upgrade", "pip", "wheel"])
    if nvidia_present() and not IS_MAC:
        run([str(py), "-m", "pip", "install", "torch", "torchvision", "torchaudio",
             "--index-url", "https://download.pytorch.org/whl/cu128"])
    run([str(py), "-m", "pip", "install", "-r", str(source / "requirements.txt")])
    launcher = ROOT / ("start_comfyui.bat" if IS_WIN else "start_comfyui.sh")
    if IS_WIN:
        content = f'@echo off\n"{py}" "{source / "main.py"}" --listen 127.0.0.1 --port 8188\n'
    else:
        content = f'#!/bin/sh\n"{py}" "{source / "main.py"}" --listen 127.0.0.1 --port 8188\n'
    launcher.write_text(content, encoding="utf-8")
    if not IS_WIN:
        launcher.chmod(0o755)


def downloads_dirs():
    paths = [Path.home() / "Downloads"]
    return list(dict.fromkeys(p for p in paths if p.exists()))


def safe_extract(archive: Path, destination: Path):
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            target = (destination / info.filename).resolve()
            if root not in target.parents and target != root:
                raise ValueError(f"Unsafe archive path: {info.filename}")
            if info.file_size > 2_000_000_000:
                raise ValueError(f"Oversized archive member: {info.filename}")
        zf.extractall(destination)


def import_research():
    log("\n[6/7] Importing compatible research source packs")
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    target = ROOT / "optional_research"
    target.mkdir(exist_ok=True)
    imported = []
    for pack in data["packs"]:
        if not pack.get("installable"):
            continue
        source = next((d / pack["archive"] for d in downloads_dirs()
                       if (d / pack["archive"]).exists()), None)
        destination = target / pack["id"]
        if not source:
            continue
        if not destination.exists():
            safe_extract(source, destination)
        imported.append(pack["id"])
    (target / "installed.json").write_text(json.dumps({"packs": imported}, indent=2),
                                            encoding="utf-8")


def desktop_dirs():
    paths = [Path.home() / "Desktop"]
    if IS_WIN:
        for key in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
            if os.getenv(key):
                paths.append(Path(os.environ[key]) / "Desktop")
        paths.append(Path.home() / "OneDrive/Desktop")
    elif IS_MAC:
        paths.append(Path.home() / "Library/CloudStorage/OneDrive-Personal/Desktop")
    result = []
    for path in paths:
        if path.exists() and path.resolve() not in [p.resolve() for p in result]:
            result.append(path)
    return result


def create_shortcuts():
    log("\n[7/7] Creating desktop shortcuts")
    for folder in desktop_dirs():
        if IS_WIN:
            link = folder / "Companion Studio Pro.lnk"
            target = venv_python().with_name("pythonw.exe")
            launcher = ROOT / "launch_app.py"
            script = (f'$w=New-Object -ComObject WScript.Shell;$s=$w.CreateShortcut("{link}");'
                      f'$s.TargetPath="{target}";$s.Arguments=\'"{launcher}"\';'
                      f'$s.WorkingDirectory="{ROOT}";$s.Save()')
            run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script])
        else:
            suffix = ".command" if IS_MAC else ".desktop"
            path = folder / f"Companion Studio Pro{suffix}"
            path.write_text(f'#!/bin/sh\ncd "{ROOT}"\n"{venv_python()}" "{ROOT / "launch_app.py"}"\n',
                            encoding="utf-8")
            path.chmod(0o755)
        log(f"  [ok] Shortcut: {folder}")


def main():
    parser = argparse.ArgumentParser(description="Install Companion Studio Pro locally")
    parser.add_argument("--minimal", action="store_true",
                        help="install only the editor, renderer, and local API")
    parser.add_argument("--gpu", action="store_true",
                        help="compatibility alias; full AI installation is the default")
    parser.add_argument("--skip-models", action="store_true",
                        help="install engines without downloading the Ollama model")
    parser.add_argument("--import-research", action="store_true")
    parser.add_argument("--yes", action="store_true", help="retained for unattended compatibility")
    parser.add_argument("--no-shortcuts", action="store_true")
    parser.add_argument("--launch", action="store_true")
    args = parser.parse_args()
    LOG.write_text("Companion Studio Pro complete installer\n", encoding="utf-8")
    ensure_python()
    log(f"Companion Studio Pro - {platform.system()} {platform.machine()}")
    install_core(ensure_node())
    engines = {"ollama": False, "comfyui": False, "ocr": False}
    if not args.minimal:
        install_gpu()
        engines["ocr"] = optional_step("Tesseract OCR", install_ocr)
        engines["ollama"] = optional_step(
            "Ollama" + ("" if args.skip_models else " + qwen2.5:3b"),
            lambda: install_ollama(not args.skip_models))
        engines["comfyui"] = optional_step("ComfyUI", install_comfyui)
    if args.import_research:
        optional_step("research source import", import_research)
    if not args.no_shortcuts:
        optional_step("desktop shortcuts", create_shortcuts)
    state = {"platform": platform.platform(), "python": platform.python_version(),
             "full_install": not args.minimal, "engines": engines,
             "warnings": WARNINGS, "root": str(ROOT)}
    (ROOT / "install-state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    log("\nInstallation complete. Use the Companion Studio Pro shortcut to start.")
    if WARNINGS:
        log("Some independent engines need attention; see install.log. The core app is ready.")
    if args.launch:
        subprocess.Popen([str(venv_python()), str(ROOT / "launch_app.py")], cwd=ROOT)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        log(f"\nCore installation stopped (exit {exc.returncode}). See install.log.")
        raise SystemExit(exc.returncode)
