"""Dynamic, story-based quest generation (core/quest_system.py).

The LLM call is mocked -- these tests verify the JSON parsing, DB write, and
fallback-to-templated behavior, not any live model.
"""
import json
from unittest.mock import patch

from core.quest_system import generate_dynamic_quest, generate_quest, get_active_quests


def test_generate_dynamic_quest_uses_llm_json(temp_db):
    fake_json = json.dumps({
        "title": "The Sealed Letter",
        "description": "Aria must deliver the blood-marked letter from the tavern before dawn.",
        "hint": "Ask the innkeeper who left it.",
        "reward": "a silver locket",
    })
    with patch("core.chat_engine.send_to_llm", return_value=fake_json):
        q = generate_dynamic_quest(
            "Aria",
            history=[{"role": "assistant", "content": "A sealed letter arrives marked in blood."}],
        )
    assert q["dynamic"] is True
    assert q["title"] == "The Sealed Letter"
    active = get_active_quests("Aria")
    assert any(a["title"] == "The Sealed Letter" for a in active)
    # Rewards come from the progression system, not the LLM's free text.
    assert q["reward_data"]["label"]
    assert any(a["reward"] == q["reward_data"]["label"] for a in active)


def test_generate_dynamic_quest_handles_markdown_fenced_json(temp_db):
    fake_response = (
        "Sure, here's a quest:\n```json\n"
        '{"title": "Debt Collector", "description": "Recover the coin owed by the merchant guild.", '
        '"hint": "Visit the guild hall.", "reward": "60 gold"}\n```'
    )
    with patch("core.chat_engine.send_to_llm", return_value=fake_response):
        q = generate_dynamic_quest("Bram", history=[])
    assert q["dynamic"] is True
    assert q["title"] == "Debt Collector"


def test_generate_dynamic_quest_falls_back_on_unparseable_response(temp_db):
    with patch("core.chat_engine.send_to_llm", return_value="I cannot help with that."):
        q = generate_dynamic_quest("Cass", history=[])
    assert q["dynamic"] is False
    assert q["id"]
    active = get_active_quests("Cass")
    assert len(active) == 1


def test_generate_dynamic_quest_falls_back_when_llm_raises(temp_db):
    with patch("core.chat_engine.send_to_llm", side_effect=ConnectionError("no LM Studio")):
        q = generate_dynamic_quest("Dex", history=[])
    assert q["dynamic"] is False
    active = get_active_quests("Dex")
    assert len(active) == 1


def test_generate_quest_templated_still_works(temp_db):
    q = generate_quest("Eve", qtype="combat")
    assert q["type"] == "combat"
    active = get_active_quests("Eve")
    assert active[0]["quest_type"] == "combat"


def _make_character(name):
    from core.storage import get_conn
    conn = get_conn()
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(characters)")}
    fields = {"name": name}
    if "created_at" in cols:
        fields["created_at"] = "2026-01-01T00:00:00"
    cur = conn.execute(
        f"INSERT INTO characters ({','.join(fields)}) VALUES ({','.join('?' * len(fields))})", tuple(fields.values())
    )
    conn.commit(); conn.close()
    return cur.lastrowid


def test_same_named_characters_do_not_share_quests(temp_db):
    first, second = _make_character("Aria"), _make_character("Aria")
    generate_quest("Aria", qtype="daily", title="First's errand", character_id=first)
    assert [q["title"] for q in get_active_quests("Aria", first)] == ["First's errand"]
    assert get_active_quests("Aria", second) == []


def test_legacy_quests_are_assigned_to_oldest_namesake(temp_db):
    import core.storage as storage
    first, second = _make_character("Bram"), _make_character("Bram")
    generate_quest("Bram", qtype="daily", title="Old quest")  # no owner, as before the migration
    storage.init_db()
    assert [q["title"] for q in get_active_quests("Bram", first)] == ["Old quest"]
    assert get_active_quests("Bram", second) == []


def test_deleting_one_namesake_keeps_the_others_quests(temp_db):
    import core.storage as storage
    first, second = _make_character("Cyra"), _make_character("Cyra")
    generate_quest("Cyra", qtype="daily", title="Keep me", character_id=second)
    storage.delete_character(first)
    assert [q["title"] for q in get_active_quests("Cyra", second)] == ["Keep me"]
