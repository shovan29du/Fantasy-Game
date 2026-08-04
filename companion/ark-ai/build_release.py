#!/usr/bin/env python3
"""Build a clean cross-platform ARK AI release ZIP."""

from pathlib import Path
import argparse
import stat
import zipfile

ROOT = Path(__file__).resolve().parent
EXCLUDED_DIRS = {".git", ".pytest_cache", "__pycache__", "dist", "venv", "workspace"}
EXCLUDED_FILES = {".env", "ark_ai.db", "realzip.db", "config.json"}
EXECUTABLE_SUFFIXES = {".command", ".sh"}


def included_files():
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if path.is_file() and path.name not in EXCLUDED_FILES and path.suffix not in {".pyc", ".db"}:
            yield path, relative


def build(output):
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, relative in included_files():
            info = zipfile.ZipInfo.from_file(path, relative.as_posix())
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if path.suffix in EXECUTABLE_SUFFIXES else 0o644
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | mode) << 16
            with path.open("rb") as source, archive.open(info, "w") as target:
                target.write(source.read())
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", default=ROOT / "dist" / "Ark_AI_Updated_Installer.zip")
    args = parser.parse_args()
    print(build(args.output))
