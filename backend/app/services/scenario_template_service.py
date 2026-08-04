"""Scenario template persistence and loading helpers."""
from __future__ import annotations

import random
import re

from core.storage import get_conn, init_db, now_iso


RANDOM_CHARACTER_NAMES = [
    "Aelira", "Bram", "Cerys", "Dorian", "Elowen", "Finn", "Kael",
    "Lyra", "Mira", "Nyx", "Orin", "Rowan", "Selene", "Talia", "Varek",
]


def save_scenario_template(name: str, scenario: str) -> None:
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Template name is required.")
    if not scenario.strip():
        raise ValueError("Scenario text is required.")
    init_db()
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO scenario_templates (name, scenario, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
              scenario=excluded.scenario,
              created_at=excluded.created_at
            """,
            (clean_name, scenario.strip(), now_iso()),
        )
        conn.commit()
    finally:
        conn.close()


def list_scenario_templates() -> list[dict]:
    init_db()
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT id, name, scenario, created_at FROM scenario_templates ORDER BY name"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def delete_scenario_template(template_id: int) -> None:
    init_db()
    conn = get_conn()
    try:
        conn.execute("DELETE FROM scenario_templates WHERE id=?", (template_id,))
        conn.commit()
    finally:
        conn.close()


def render_template_scenario(scenario: str, character_name: str | None = None) -> tuple[str, str]:
    """Return scenario text with randomized character placeholder and User player name.

    Supported placeholders:
    - {character}, {character_name}, {{character}}, {{character_name}}
    - {user}, {user_name}, {player}, {{user}}, {{user_name}}, {{player}}

    If a saved template did not use placeholders, the text is returned unchanged
    except explicit player/self labels are normalized to "User".
    """
    generated_name = character_name or random.choice(RANDOM_CHARACTER_NAMES)
    rendered = scenario
    rendered = re.sub(r"\{\{?\s*(character|character_name)\s*\}?\}", generated_name, rendered, flags=re.I)
    rendered = re.sub(r"\{\{?\s*(user|user_name|player)\s*\}?\}", "User", rendered, flags=re.I)
    rendered = re.sub(r"\b(player|the player|you)\b", "User", rendered, flags=re.I)
    return rendered, generated_name
