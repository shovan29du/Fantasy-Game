"""Generate and seed knowledge documents from built-in app option catalogs."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.domain.characters.catalog import (  # noqa: E402
    ALIGNMENTS,
    ALL_PRESET_SOURCES,
    BODY_TYPES,
    CHARACTER_TAGS,
    DND_BACKGROUNDS,
    DND_RACES,
    EMOTION_STYLES,
    GENDERS,
    IMAGE_STYLES,
    MAGIC_TYPES,
    POWER_SYSTEMS,
    PROFESSIONS,
    QUIRKS_LIST,
    SKILLS_LIST,
    TRAITS_LIST,
    WEAPON_TYPES,
)
from core.storage import init_db, now_iso  # noqa: E402


KNOWLEDGE_DIR = ROOT / "knowledge" / "app_options"
DB_PATH = ROOT / "data" / "aichat_pro.db"


OPTION_GROUPS = {
    "Backgrounds": DND_BACKGROUNDS,
    "Genders": GENDERS,
    "Body Types": BODY_TYPES,
    "Professions": PROFESSIONS,
    "Weapon Types": WEAPON_TYPES,
    "Magic Types": MAGIC_TYPES,
    "Power Systems": POWER_SYSTEMS,
    "Traits": TRAITS_LIST,
    "Quirks": QUIRKS_LIST,
    "Skills": SKILLS_LIST,
    "Character Tags": CHARACTER_TAGS,
    "Emotion Styles": EMOTION_STYLES,
    "Alignments": ALIGNMENTS,
    "Image Styles": IMAGE_STYLES,
    "Preset Sources": ALL_PRESET_SOURCES,
}


def bullet_list(values: list[str]) -> str:
    return "\n".join(f"- {value}" for value in values)


def race_doc() -> str:
    lines = [
        "# AiChat Pro Race Options",
        "",
        "Generated from the app's built-in character catalog. These entries are stored as local knowledge and can also be seeded into SQLite.",
        "",
    ]
    for name, data in sorted(DND_RACES.items()):
        lines.extend(
            [
                f"## {name}",
                "",
                f"- Lore: {data.get('lore', 'No lore provided.')}",
                f"- Traits: {', '.join(data.get('traits', []))}",
                f"- Features: {', '.join(data.get('features', []))}",
                f"- Stat Bonuses: {json.dumps(data.get('stat_bonuses', {}), ensure_ascii=False)}",
                f"- Speed: {data.get('speed', 'Varies')}",
                f"- Size: {data.get('size', 'Varies')}",
                f"- Languages: {', '.join(data.get('languages', []))}",
                f"- Height: {data.get('height', 'Varies')}",
                f"- Weight: {data.get('weight', 'Varies')}",
                f"- Age Range: {data.get('age_range', 'Varies')}",
                f"- Skin Options: {', '.join(data.get('skin', []))}",
                f"- Hair Options: {', '.join(data.get('hair', []))}",
                f"- Eye Options: {', '.join(data.get('eyes', []))}",
                "",
            ]
        )
    return "\n".join(lines)


def options_doc() -> str:
    lines = [
        "# AiChat Pro Character Options",
        "",
        "Generated from the app's built-in option lists.",
        "",
    ]
    for title, values in OPTION_GROUPS.items():
        lines.extend([f"## {title}", "", bullet_list(values), ""])
    return "\n".join(lines)


def write_docs() -> list[Path]:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    docs = {
        KNOWLEDGE_DIR / "race_options.md": race_doc(),
        KNOWLEDGE_DIR / "character_options.md": options_doc(),
    }
    for path, content in docs.items():
        path.write_text(content, encoding="utf-8")
    return list(docs)


def seed_database(paths: list[Path]) -> None:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        for path in paths:
            conn.execute(
                """
                INSERT INTO knowledge_documents (path, title, content, embedding_json, indexed_at)
                VALUES (?, ?, ?, NULL, ?)
                ON CONFLICT(path) DO UPDATE SET
                  title=excluded.title,
                  content=excluded.content,
                  indexed_at=excluded.indexed_at
                """,
                (
                    str(path.relative_to(ROOT)),
                    path.stem.replace("_", " ").title(),
                    path.read_text(encoding="utf-8"),
                    now_iso(),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def main() -> int:
    paths = write_docs()
    seed_database(paths)
    print(f"Seeded {len(paths)} option knowledge documents.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
