"""
full_install.py  —  Worldweaver Multiverse Tabletop installer
=============================================================

Usage
-----
  python full_install.py                  # recommended (core + voice + media)
  python full_install.py --minimal        # core packages only, no extras
  python full_install.py --all-optional   # everything including docs / memory
  python full_install.py --no-shortcuts   # skip desktop shortcut creation
  python full_install.py --no-venv        # install into the current interpreter
  python full_install.py --help           # show this message

What it does
------------
  1. Check Python version (3.10+)
  2. Create / repair a .venv virtual environment
  3. Install core dependencies from requirements.txt
  4. Install selected optional feature packages
  5. Verify the pre-built frontend (or build it with Node if missing)
  6. Initialise the SQLite database
  7. Create desktop and Start-Menu shortcuts
  8. Print a launch summary

Port: 8501  (http://localhost:8501)
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path


# ─── constants ────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).resolve().parent
VENV      = ROOT / ".venv"
PORT      = 8501
APP_NAME  = "Worldweaver"
APP_FULL  = "Worldweaver Multiverse Tabletop"
APP_DESC  = f"AI-driven multiverse tabletop RPG — http://localhost:{PORT}"
ICON_PNG  = ROOT / "assets" / "worldweaver-512.png"
ICON_ICO  = ROOT / "assets" / "worldweaver.ico"
REQ_FILE  = ROOT / "requirements.txt"
DIST_DIR  = ROOT / "frontend" / "react_app" / "dist"

# Core packages (installed even with --minimal).
# requirements.txt is also installed and wins on version conflicts.
CORE_PACKAGES: list[str] = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.30.0",
    "requests>=2.28.0",
    "python-multipart>=0.0.9",
    "bcrypt>=4.0.0",
    "Pillow>=9.0.0",
    "psutil>=5.9.0",
    "networkx>=3.0",
]

# Optional feature groups.  Default install = voice + media.
OPTIONAL: dict[str, list[str]] = {
    "voice": [
        "edge-tts>=6.1.0",
        "SpeechRecognition>=3.10.0",
    ],
    "media": [
        "imageio-ffmpeg>=0.5.0",
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
DEFAULT_GROUPS = ["voice", "media"]


# ─── helpers ──────────────────────────────────────────────────────────────────
class InstallError(RuntimeError):
    pass


def _banner() -> None:
    width = 60
    print()
    print("=" * width)
    print(f"  {APP_FULL}")
    print(f"  Installer  —  port {PORT}")
    print("=" * width)
    print(f"  Python  : {sys.version.split()[0]}")
    print(f"  Platform: {platform.system()} {platform.machine()}")
    print(f"  Root    : {ROOT}")
    print("=" * width)
    print()


def _step(n: int, total: int, label: str) -> None:
    print(f"\n[{n}/{total}] {label}")
    print("─" * 50)


def _ok(msg: str) -> None:
    print(f"  ✓  {msg}")


def _warn(msg: str) -> None:
    print(f"  ⚠  {msg}")


def _run(cmd: list[str], *, check: bool = True, quiet: bool = False) -> int:
    display = " ".join(str(c) for c in cmd)
    if not quiet:
        print(f"  $ {display}")
    kwargs: dict = dict(cwd=ROOT)
    if quiet:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL
    result = subprocess.run(cmd, **kwargs, check=False)
    if check and result.returncode != 0:
        raise InstallError(f"Command failed (exit {result.returncode}): {display}")
    return result.returncode


# ─── step 1 – Python version ──────────────────────────────────────────────────
def check_python() -> None:
    if sys.version_info < (3, 10):
        raise InstallError(
            f"Python 3.10 or newer is required. You have {sys.version.split()[0]}.\n"
            "  Download Python from https://python.org and re-run this script."
        )
    _ok(f"Python {sys.version.split()[0]} — OK")


# ─── step 2 – virtual environment ─────────────────────────────────────────────
def _venv_python() -> Path:
    if platform.system() == "Windows":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def _pip_healthy(python: Path) -> bool:
    if not python.exists():
        return False
    rc = subprocess.run(
        [str(python), "-c", "import pip._internal.resolution.resolvelib.resolver"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode
    return rc == 0


def ensure_venv(use_venv: bool) -> Path:
    if not use_venv:
        _ok("Skipping venv — using current interpreter")
        return Path(sys.executable)

    python = _venv_python()

    # Repair a broken venv instead of silently using it
    if VENV.exists() and python.exists() and not _pip_healthy(python):
        backup = ROOT / f".venv-broken-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        _warn(f"Existing environment has a damaged pip — moving to {backup.name}")
        VENV.rename(backup)

    if not VENV.exists():
        print(f"  Creating virtual environment in {VENV.name} ...")
        _run([sys.executable, "-m", "venv", str(VENV)])

    python = _venv_python()

    if not _pip_healthy(python):
        print("  Repairing pip ...")
        _run([str(python), "-m", "ensurepip", "--upgrade", "--default-pip"])

    if not _pip_healthy(python):
        raise InstallError(
            "Could not create a working pip environment.\n"
            "  Try deleting the .venv folder and running this script again,\n"
            "  or reinstall Python from https://python.org."
        )

    _ok(f"Virtual environment ready: {VENV}")
    return python


# ─── step 3 – core dependencies ───────────────────────────────────────────────
def install_core(python: Path) -> None:
    # Upgrade pip first so the resolver works on newer package formats
    _run([str(python), "-m", "pip", "install", "--upgrade", "pip", "--quiet"], quiet=True)
    _ok("pip up to date")

    # Install from requirements.txt (canonical source of truth)
    if REQ_FILE.exists():
        print(f"  Installing from {REQ_FILE.name} ...")
        _run([str(python), "-m", "pip", "install", "-r", str(REQ_FILE), "--quiet"])
        _ok(f"requirements.txt installed")
    else:
        # Fallback: install hard-coded list
        print("  requirements.txt not found — installing core packages directly ...")
        _run([str(python), "-m", "pip", "install", "--quiet", *CORE_PACKAGES])
        _ok("Core packages installed")


# ─── step 4 – optional packages ───────────────────────────────────────────────
def install_optional(python: Path, groups: list[str]) -> None:
    if not groups:
        _ok("No optional packages selected")
        return

    packages: list[str] = []
    for g in groups:
        packages.extend(OPTIONAL.get(g, []))

    if not packages:
        _ok("No packages in selected groups")
        return

    print(f"  Groups: {', '.join(groups)}")
    _run([str(python), "-m", "pip", "install", "--quiet", *packages])
    _ok(f"{len(packages)} optional package(s) installed")


# ─── step 5 – frontend ────────────────────────────────────────────────────────
def check_frontend() -> None:
    index = DIST_DIR / "index.html"
    if index.exists():
        _ok(f"Pre-built frontend found at {DIST_DIR.relative_to(ROOT)}")
        return

    # Try to build with Node.js
    runner = shutil.which("pnpm") or shutil.which("npm")
    if not runner:
        raise InstallError(
            "The pre-built frontend is missing and Node.js was not found.\n"
            "  Either restore frontend/react_app/dist/ from the repository,\n"
            "  or install Node.js 20+ from https://nodejs.org and re-run."
        )

    frontend_dir = ROOT / "frontend" / "react_app"
    print(f"  Building frontend with {Path(runner).name} ...")
    subprocess.check_call([runner, "install"], cwd=frontend_dir)
    subprocess.check_call([runner, "run", "build"], cwd=frontend_dir)
    _ok("Frontend built successfully")


# ─── step 6 – database initialisation ────────────────────────────────────────
def init_database(python: Path) -> None:
    # Call the app's own DB bootstrap so all tables exist before first launch
    bootstrap = textwrap.dedent("""
        import sys
        sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
        try:
            from backend.app.core.database import init_db
            init_db()
            print("Database initialised.")
        except Exception as exc:
            print(f"Warning: DB init skipped — {exc}")
    """)
    tmp = ROOT / "_db_init_tmp.py"
    tmp.write_text(bootstrap, encoding="utf-8")
    try:
        result = subprocess.run(
            [str(python), str(tmp)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        msg = (result.stdout or result.stderr or "").strip()
        if result.returncode == 0:
            _ok(msg or "Database ready")
        else:
            _warn(f"DB init returned non-zero: {msg}")
    finally:
        tmp.unlink(missing_ok=True)


# ─── step 7 – shortcuts ───────────────────────────────────────────────────────
def _ps_shortcut(lnk: Path, target: Path, working: Path, desc: str) -> bool:
    """Create a .lnk shortcut via PowerShell. Returns True on success."""
    lnk.parent.mkdir(parents=True, exist_ok=True)
    icon_part = f"$s.IconLocation='{str(ICON_ICO).replace(chr(39), '')}';  " if ICON_ICO.exists() else ""
    ps_cmd = (
        "$w=New-Object -ComObject WScript.Shell;"
        f"$s=$w.CreateShortcut('{str(lnk).replace(chr(39), chr(96))}');"
        f"$s.TargetPath='{str(target).replace(chr(39), chr(96))}';"
        f"$s.WorkingDirectory='{str(working).replace(chr(39), chr(96))}';"
        f"{icon_part}"
        f"$s.Description='{desc.replace(chr(39), '')}';$s.Save()"
    )
    rc = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
        capture_output=True,
    ).returncode
    return rc == 0


def write_windows_shortcuts() -> None:
    target  = ROOT / "run_app.bat"
    desktops: list[Path] = []

    # OneDrive desktops (may be on a different drive or named "OneDrive - Corp")
    for env_key in ("OneDriveCommercial", "OneDrive", "OneDriveConsumer"):
        val = os.environ.get(env_key, "")
        if val:
            candidate = Path(val) / "Desktop"
            if candidate.is_dir() and candidate not in desktops:
                desktops.append(candidate)
                _ok(f"OneDrive Desktop detected: {candidate}")

    # Fallback: default Desktop and common OneDrive paths
    for fallback in [
        Path.home() / "Desktop",
        Path.home() / "OneDrive" / "Desktop",
    ]:
        if fallback.is_dir() and fallback not in desktops:
            desktops.append(fallback)

    # Start Menu
    start_menu = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"

    created = 0
    for desktop in desktops:
        lnk = desktop / f"{APP_FULL}.lnk"
        if _ps_shortcut(lnk, target, ROOT, APP_DESC):
            _ok(f"Shortcut → {lnk}")
            created += 1
        else:
            _warn(f"Could not create shortcut in {desktop}")

    if start_menu.is_dir():
        lnk = start_menu / f"{APP_FULL}.lnk"
        if _ps_shortcut(lnk, target, ROOT, APP_DESC):
            _ok(f"Start Menu → {lnk}")
        else:
            _warn("Could not create Start Menu shortcut")

    if created == 0:
        _warn("No Desktop folder found — launch with run_app.bat")


def write_macos_shortcut() -> None:
    desktop = Path.home() / "Desktop"
    if not desktop.is_dir():
        _warn("Desktop folder not found — skipping macOS shortcut")
        return
    launcher = desktop / f"{APP_FULL}.command"
    launcher.write_text(
        f'#!/bin/bash\ncd "{ROOT}"\n./run_app.sh\n',
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    _ok(f"macOS launcher → {launcher}")


def write_linux_shortcut() -> None:
    desktop = Path.home() / "Desktop"
    if not desktop.is_dir():
        # Also try XDG Desktop
        xdg = os.environ.get("XDG_DESKTOP_DIR", "")
        if xdg and Path(xdg).is_dir():
            desktop = Path(xdg)
        else:
            _warn("Desktop folder not found — skipping Linux shortcut")
            return
    entry = desktop / f"{APP_FULL}.desktop"
    entry.write_text(
        "[Desktop Entry]\n"
        "Version=1.0\n"
        "Type=Application\n"
        f"Name={APP_FULL}\n"
        f"Comment={APP_DESC}\n"
        f"Exec={ROOT / 'run_app.sh'}\n"
        f"Path={ROOT}\n"
        f"Icon={ICON_PNG}\n"
        "Terminal=true\n"
        "Categories=Game;RolePlaying;\n",
        encoding="utf-8",
    )
    entry.chmod(0o755)
    _ok(f"Linux .desktop entry → {entry}")


def write_shortcuts() -> None:
    system = platform.system()
    if system == "Windows":
        write_windows_shortcuts()
    elif system == "Darwin":
        write_macos_shortcut()
    elif system == "Linux":
        write_linux_shortcut()
    else:
        _warn(f"Unknown platform '{system}' — skipping shortcut creation")


# ─── summary ──────────────────────────────────────────────────────────────────
def _summary(python: Path) -> None:
    width = 60
    print()
    print("=" * width)
    print(f"  Installation complete!")
    print("=" * width)
    print(f"  App   : {APP_FULL}")
    print(f"  URL   : http://localhost:{PORT}")
    print(f"  Venv  : {python.parent.parent if python != Path(sys.executable) else 'system'}")
    print()
    system = platform.system()
    if system == "Windows":
        print("  To launch:")
        print("    • Double-click 'run_app.bat'")
        print("    • Or use the Desktop / Start Menu shortcut")
    elif system == "Darwin":
        print("  To launch:")
        print("    • Double-click the .command file on your Desktop")
        print("    • Or run:  ./run_app.sh")
    else:
        print("  To launch:")
        print("    ./run_app.sh")
    print()
    print("  Tip: Start LM Studio on port 1234 before opening the")
    print("       game for local AI chat.")
    print("=" * width)
    print()


# ─── argument parsing ─────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python full_install.py",
        description=f"Install {APP_FULL} (port {PORT})",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(f"""\
            Optional feature groups:
              voice      edge-tts, SpeechRecognition
              media      imageio-ffmpeg (bundled ffmpeg for video/animation)
              documents  pypdf, python-docx, reportlab
              memory     chromadb, sentence-transformers
              dev        pytest

            Default groups: {', '.join(DEFAULT_GROUPS)}
        """),
    )
    p.add_argument(
        "--minimal",
        action="store_true",
        help="Install core packages only (no optional feature packages)",
    )
    p.add_argument(
        "--all-optional",
        action="store_true",
        help="Install all optional feature packages",
    )
    p.add_argument(
        "--groups",
        metavar="GROUP",
        nargs="+",
        choices=list(OPTIONAL),
        help="Install specific optional groups (e.g. --groups voice media)",
    )
    p.add_argument(
        "--no-shortcuts",
        action="store_true",
        help="Skip desktop shortcut creation",
    )
    p.add_argument(
        "--no-venv",
        action="store_true",
        help="Install into the current Python interpreter instead of .venv",
    )
    p.add_argument(
        "--no-db",
        action="store_true",
        help="Skip database initialisation step",
    )
    return p.parse_args()


# ─── main ─────────────────────────────────────────────────────────────────────
def main() -> int:
    args = parse_args()

    _banner()

    # Decide which optional groups to install
    if args.minimal:
        optional_groups: list[str] = []
    elif args.all_optional:
        optional_groups = list(OPTIONAL)
    elif args.groups:
        optional_groups = args.groups
    else:
        optional_groups = DEFAULT_GROUPS

    total_steps = 7 - (1 if args.no_shortcuts else 0) - (1 if args.no_db else 0)
    step = 0

    def next_step(label: str) -> None:
        nonlocal step
        step += 1
        _step(step, total_steps, label)

    try:
        next_step("Checking Python version")
        check_python()

        next_step("Setting up virtual environment")
        python = ensure_venv(use_venv=not args.no_venv)

        next_step("Installing core dependencies")
        install_core(python)

        next_step(f"Installing optional packages [{', '.join(optional_groups) or 'none'}]")
        install_optional(python, optional_groups)

        next_step("Verifying frontend build")
        check_frontend()

        if not args.no_db:
            next_step("Initialising database")
            init_database(python)

        if not args.no_shortcuts:
            next_step("Creating desktop shortcuts")
            write_shortcuts()

        _summary(python)
        return 0

    except InstallError as exc:
        print(f"\n[ERROR] {exc}\n", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInstallation cancelled.", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"\n[UNEXPECTED ERROR] {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
