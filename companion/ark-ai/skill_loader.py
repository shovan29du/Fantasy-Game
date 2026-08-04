"""Discover portable SKILL.md packages for Ark AI.

Skills are deliberately data-only: selecting one adds its instructions to the
model context, but never executes bundled scripts automatically.
"""

from pathlib import Path
import re


SKILLS_DIR = Path(__file__).resolve().parent / "skills"
MAX_SKILL_CHARS = 48_000


def _frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not match:
        return {}, text
    values = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip() in {"name", "description"}:
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values, text[match.end():]


def discover_skills(root=None):
    """Return safe metadata for every top-level installed skill."""
    base = Path(root) if root else SKILLS_DIR
    if not base.is_dir():
        return []
    skills = []
    for path in sorted(base.glob("*/SKILL.md")):
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        meta, instructions = _frontmatter(raw)
        slug = path.parent.name
        name = meta.get("name") or slug
        description = meta.get("description") or "Installed local skill"
        skills.append({
            "id": "skill:" + slug,
            "name": name.replace("-", " ").strip().title(),
            "tag": "skill",
            "mode": "research" if "research" in slug else "chat",
            "icon": "🧩",
            "desc": description[:320],
            "prompt": instructions.strip()[:MAX_SKILL_CHARS],
            "source": "SenseNova Skills",
        })
    return skills


def find_skill(skill_id, root=None):
    return next((skill for skill in discover_skills(root) if skill["id"] == skill_id), None)
