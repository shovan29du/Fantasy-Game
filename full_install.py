"""Cross-platform installer for AiChat Pro.

Creates a local virtual environment, installs all Python dependencies,
installs feature extras, seeds local knowledge, and writes launch shortcuts.
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
APP_NAME = "Worldweaver Multiverse Tabletop"
ICON_PNG = ROOT / "assets" / "worldweaver-512.png"
ICON_ICO = ROOT / "assets" / "worldweaver.ico"

REQUIRED_PACKAGES = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.30.0",
    "requests>=2.28.0",
    "python-multipart>=0.0.9",
    "bcrypt>=4.0.0",
    "Pillow>=9.0.0",
    "psutil>=5.9.0",
    "networkx>=3.0",
]

OPTIONAL_PACKAGES = {
    "voice": [
        "edge-tts>=6.1.0",
        "SpeechRecognition>=3.10.0",
        "pyttsx3>=2.90",
        "gTTS>=2.5.0",
    ],
    "media": [
        "imageio-ffmpeg>=0.5.0",  # bundled ffmpeg binary for Text-to-Animation/Video
    ],
    "documents": [
        "pypdf>=4.0.0",
        "python-docx>=1.1.0",
        "reportlab>=4.0.0",
    ],
    "memory": [
        "chromadb>=0.4.0",
        "sentence-transformers>=2.2.0",
    ],
    "dev": [
        "pytest>=8.0.0",
    ],
}


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.check_call(command, cwd=ROOT)


def venv_python() -> Path:
    if platform.system() == "Windows":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def pip_is_healthy(python: Path) -> bool:
    """Exercise pip's resolver imports; `pip --version` alone misses mixed installs."""
    if not python.exists():
        return False
    check = subprocess.run(
        [str(python), "-c", "import pip._internal.resolution.resolvelib.resolver"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return check.returncode == 0

def ensure_venv() -> Path:
    """Create the environment, preserving and replacing it if pip is damaged."""
    python = venv_python()
    if VENV.exists() and python.exists():
        if not pip_is_healthy(python):
            from datetime import datetime
            backup = ROOT / f".venv-broken-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            print(f"The existing Python environment is damaged; preserving it as {backup.name}")
            VENV.rename(backup)
    if not VENV.exists():
        run([sys.executable, "-m", "venv", str(VENV)])
    python = venv_python()
    if not pip_is_healthy(python):
        run([str(python), "-m", "ensurepip", "--upgrade", "--default-pip"])
    if not pip_is_healthy(python):
        raise RuntimeError("Python created an unusable pip environment. Repair or reinstall Python, then retry.")
    return python


def install_dependencies(python: Path) -> None:
    run([str(python), "-m", "pip", "--version"])
    run([str(python), "-m", "pip", "install", *REQUIRED_PACKAGES])
    if (ROOT / "requirements.txt").exists():
        run([str(python), "-m", "pip", "install", "-r", "requirements.txt"])


def selected_optional_groups() -> list[str]:
    """Install every supported feature automatically."""
    return list(OPTIONAL_PACKAGES)


def install_optional_dependencies(python: Path, groups: list[str]) -> None:
    packages: list[str] = []
    for group in groups:
        packages.extend(OPTIONAL_PACKAGES[group])
    if packages:
        run([str(python), "-m", "pip", "install", *packages])


def build_frontend() -> None:
    """Build with Node when available; otherwise use the packaged build."""
    frontend = ROOT / "frontend" / "react_app"
    dist = frontend / "dist" / "index.html"
    if dist.exists():
        print("Packaged frontend ready; Node.js is not required.")
        return
    runner = shutil.which("pnpm") or shutil.which("npm")
    if not runner:
        raise RuntimeError("Node.js 20+ is required because the packaged frontend is missing.")
    install_args = [runner, "install"]
    print("+", " ".join(install_args))
    subprocess.check_call(install_args, cwd=frontend)
    subprocess.check_call([runner, "run", "build"], cwd=frontend)

def seed_knowledge(python: Path) -> None:
    run([str(python), "tools/seed_knowledge.py"])


def write_windows_shortcut() -> None:
    """Create real icon shortcuts in normal and OneDrive Desktop folders."""
    candidates = [Path.home() / "Desktop"]
    for key in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        if os.environ.get(key):
            candidates.append(Path(os.environ[key]) / "Desktop")
    candidates.extend([Path.home() / "OneDrive" / "Desktop", Path.home() / "OneDrive" / "Documents" / "Desktop"])
    created: set[Path] = set()
    for desktop in candidates:
        if not desktop.exists():
            continue
        shortcut = desktop / f"{APP_NAME}.lnk"
        if shortcut in created:
            continue
        shortcut_value = str(shortcut).replace("'", "''")
        target_value = str(ROOT / "run_app.bat").replace("'", "''")
        root_value = str(ROOT).replace("'", "''")
        icon_value = f"{ICON_ICO},0".replace("'", "''")
        ps = (
            "$w=New-Object -ComObject WScript.Shell;"
            f"$s=$w.CreateShortcut('{shortcut_value}');"
            f"$s.TargetPath='{target_value}';$s.WorkingDirectory='{root_value}';"
            f"$s.IconLocation='{icon_value}';"
            "$s.Description='Worldweaver multiverse tabletop RPG';$s.Save()"
        )
        run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps])
        created.add(shortcut)
        print(f"Created colourful desktop icon: {shortcut}")
    if not created:
        print("No Desktop folder was found; launch with run_app.bat.")

def write_macos_shortcut() -> None:
    desktop = Path.home() / "Desktop"
    if not desktop.exists():
        return
    launcher = desktop / "Worldweaver Multiverse Tabletop.command"
    launcher.write_text(
        f'#!/bin/bash\ncd "{ROOT}"\n./run_app.sh\n',
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    print(f"Created macOS launcher: {launcher}")


def write_linux_shortcut() -> None:
    desktop = Path.home() / "Desktop"
    if not desktop.exists():
        return
    launcher = desktop / "Worldweaver Multiverse Tabletop.desktop"
    launcher.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Worldweaver Multiverse Tabletop\n"
        f"Exec={ROOT / 'run_app.sh'}\n"
        f"Path={ROOT}\n"
        f"Icon={ICON_PNG}\n"
        "Terminal=true\n"
        "Categories=Game;RolePlaying;\n",
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    print(f"Created Linux desktop entry: {launcher}")


def write_shortcut() -> None:
    system = platform.system()
    if system == "Windows":
        write_windows_shortcut()
    elif system == "Darwin":
        write_macos_shortcut()
    elif system == "Linux":
        write_linux_shortcut()


def main() -> int:
    if sys.version_info < (3, 10):
        print("Python 3.10+ is required.")
        return 1
    python = ensure_venv()
    install_dependencies(python)
    install_optional_dependencies(python, selected_optional_groups())
    build_frontend()
    seed_knowledge(python)
    write_shortcut()
    print("\nInstall complete.")
    print("Run Windows: run_app.bat or the desktop icon")
    print("Run macOS/Linux: ./run_app.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

