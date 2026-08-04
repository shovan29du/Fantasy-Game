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
    assert any("silver locket" in a["reward"] for a in active)


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
