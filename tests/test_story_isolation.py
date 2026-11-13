"""The same character name in a different story is a different character:
memories and relationship tracking must not carry over between stories."""
import core.memory_engine as memory_module
from core.relationship_engine import ensure_relationship, get_relationship, record_interaction


def _engine():
    return getattr(memory_module, "memory_engine", None) or memory_module.MemoryEngine()


def test_auto_memories_stay_in_their_story(temp_db):
    engine = _engine()
    engine.store_fact("Aria betrayed the harbour guild", source="auto", character_name="Aria", session_id="game-a")
    engine.store_fact("Aria saved the mountain village", source="auto", character_name="Aria", session_id="game-b")

    in_a = engine.build_memory_context(query="Aria", character_name="Aria", session_id="game-a")
    in_b = engine.build_memory_context(query="Aria", character_name="Aria", session_id="game-b")

    assert "harbour guild" in in_a and "mountain village" not in in_a
    assert "mountain village" in in_b and "harbour guild" not in in_b


def test_legacy_auto_memories_do_not_reach_new_stories(temp_db):
    engine = _engine()
    engine.store_fact("Aria once ruled the old capital", source="auto", character_name="Aria")
    assert "old capital" not in engine.build_memory_context(query="Aria capital", character_name="Aria", session_id="game-new")


def test_facts_saved_without_a_story_are_shared(temp_db):
    engine = _engine()
    engine.store_fact("The player prefers short replies", source="manual", importance=0.9)
    assert "short replies" in engine.build_memory_context(query="replies", session_id="game-any")


def test_story_identity_separates_relationships(temp_db):
    from backend.app.main import _story_identity

    first, second = _story_identity("Aria", "game-a"), _story_identity("Aria", "game-b")
    assert first != second
    assert _story_identity("Aria", "default") == "Aria"

    ensure_relationship(first)
    ensure_relationship(second)
    record_interaction(first, "positive", "helped")
    assert get_relationship(first)["interaction_count"] == 1
    assert get_relationship(second)["interaction_count"] == 0
