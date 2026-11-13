"""Journal: notes, memory management, people and recap (core/journal.py)."""
from unittest.mock import patch

import pytest

import core.journal as journal
import core.memory_engine as memory_module
from core.relationship_engine import ensure_relationship, record_interaction
from core.storage import get_conn, now_iso


def _engine():
    return memory_module.MemoryEngine()


def _fact(engine, text, session_id="", source="journal", **kw):
    engine.store_fact(text, source=source, session_id=session_id, **kw)
    conn = get_conn()
    fid = conn.execute("SELECT MAX(id) FROM memory_facts").fetchone()[0]
    conn.close()
    return fid


# ── notes ────────────────────────────────────────────────────────────────

def test_notes_are_scoped_to_their_story_and_searchable(temp_db):
    journal.create_note("game-a", "Smuggler's cove", "Meet Corvin at midnight", ["clue", "Corvin"])
    journal.create_note("game-b", "Other story", "Unrelated")
    assert [n["title"] for n in journal.list_notes("game-a")] == ["Smuggler's cove"]
    assert journal.list_notes("game-a", query="corvin midnight")
    assert journal.list_notes("game-a", query="zebra") == []
    assert journal.list_notes("game-a", tag="clue")[0]["tags"] == ["clue", "corvin"]


def test_pinned_notes_sort_first_and_update_changes_fields(temp_db):
    first = journal.create_note("s", "First", "a")
    second = journal.create_note("s", "Second", "b")
    journal.update_note(first["id"], {"pinned": True})
    assert [n["title"] for n in journal.list_notes("s")] == ["First", "Second"]
    changed = journal.update_note(second["id"], {"title": "Renamed", "kind": "todo", "tags": "x, y, x"})
    assert (changed["title"], changed["kind"], changed["tags"]) == ("Renamed", "todo", ["x", "y"])
    assert journal.update_note(9999, {"title": "x"}) is None


def test_note_validation(temp_db):
    with pytest.raises(ValueError):
        journal.create_note("s", "", "")
    with pytest.raises(ValueError):
        journal.create_note("s", "t", "b", kind="bogus")
    note = journal.create_note("s", "t", "b")
    with pytest.raises(ValueError):
        journal.update_note(note["id"], {"title": "", "body": ""})
    assert journal.delete_note(note["id"]) and not journal.delete_note(note["id"])


# ── memory ───────────────────────────────────────────────────────────────

def test_memory_list_matches_what_the_story_can_recall(temp_db):
    engine = _engine()
    mine = _fact(engine, "Marta owes the player a favour", session_id="game-a")
    shared = _fact(engine, "The player likes short replies")
    other = _fact(engine, "Secret of the other story", session_id="game-b")
    auto_old = _fact(engine, "Old auto-captured exchange", source="auto")

    ids = {m["id"] for m in journal.list_memory("game-a")}
    assert ids == {mine, shared}
    assert other not in ids and auto_old not in ids
    assert {m["id"] for m in journal.list_memory("game-a", view="legacy")} == {auto_old}
    # the list and the storyteller's recall agree
    context = engine.build_memory_context(query="favour replies", session_id="game-a")
    assert "favour" in context and "Secret of the other story" not in context


def test_pin_level_edit_and_delete(temp_db):
    engine = _engine()
    fid = _fact(engine, "Marta owes the player a favour", session_id="g")
    item = journal.update_memory(fid, {"pinned": True})
    assert item["pinned"] and item["importance"] == 1.0 and item["level"] == "important"
    item = journal.update_memory(fid, {"pinned": False, "level": "minor"})
    assert not item["pinned"] and item["level"] == "minor"
    item = journal.update_memory(fid, {"fact": "Marta forgave the debt", "memory_type": "event"})
    assert item["fact"] == "Marta forgave the debt" and item["memory_type"] == "event"
    with pytest.raises(ValueError):
        journal.update_memory(fid, {"memory_type": "nonsense"})
    with pytest.raises(ValueError):
        journal.update_memory(fid, {"fact": "  "})
    assert journal.delete_memory(fid) and journal.update_memory(fid, {"fact": "x"}) is None


def test_adopting_a_legacy_memory_makes_it_recallable(temp_db):
    engine = _engine()
    fid = _fact(engine, "The harbour master hates pirates", source="auto")
    assert fid not in {m["id"] for m in journal.list_memory("g")}
    journal.update_memory(fid, {"session_id": "g"})
    assert fid in {m["id"] for m in journal.list_memory("g")}


def test_pinned_memories_survive_decay_and_pruning(temp_db):
    engine = _engine()
    pinned = _fact(engine, "Never forget the red door", session_id="g")
    plain = _fact(engine, "Passing remark", session_id="g")
    journal.update_memory(pinned, {"pinned": True})
    conn = get_conn()
    conn.execute("UPDATE memory_facts SET created_at='2020-01-01T00:00:00', last_accessed='2020-01-01T00:00:00'")
    conn.commit(); conn.close()
    engine.apply_decay(0.05)
    engine.prune(keep=0)
    remaining = {m["id"] for m in journal.list_memory("g")}
    assert remaining == {pinned}


def test_memory_filters(temp_db):
    engine = _engine()
    _fact(engine, "Aria prefers tea", session_id="g", memory_type="preference")
    _fact(engine, "The bridge collapsed", session_id="g", memory_type="event")
    assert [m["memory_type"] for m in journal.list_memory("g", memory_type="event")] == ["event"]
    assert len(journal.list_memory("g", query="aria tea")) == 1


# ── people ───────────────────────────────────────────────────────────────

def test_people_are_per_story_and_include_recorded_facts(temp_db):
    name_a, name_b = "Marta [game-a]", "Marta [game-b]"
    ensure_relationship(name_a)
    ensure_relationship(name_b)
    record_interaction(name_a, "gift", "gave her a ring")
    conn = get_conn()
    conn.execute("INSERT INTO npc_memory (character_id, npc_name, fact, session_id, created_at) VALUES (1,'Marta','Runs the Gull Inn','game-a',?)", (now_iso(),))
    conn.execute("INSERT INTO npc_memory (character_id, npc_name, fact, session_id, created_at) VALUES (1,'Corvin','Smuggler','game-a',?)", (now_iso(),))
    conn.commit(); conn.close()

    people = {p["name"]: p for p in journal.people("game-a", character_id=1)}
    assert set(people) == {"Marta", "Corvin"}
    assert people["Marta"]["trust"] == 58 and people["Marta"]["facts"] == ["Runs the Gull Inn"]
    assert people["Marta"]["events"][0]["sentiment"] == "gift"
    assert people["Corvin"]["trust"] is None
    assert [p["name"] for p in journal.people("game-b")] == ["Marta"]
    assert journal.people("game-b")[0]["trust"] == 50


# ── recap ────────────────────────────────────────────────────────────────

def test_recap_prompt_needs_some_story(temp_db):
    assert journal.recap_prompt("empty") is None
    conn = get_conn()
    for role, text in [("assistant", "You arrive at the harbour."), ("user", "I look for Marta.")]:
        conn.execute("INSERT INTO messages (session_id, role, content, created_at) VALUES ('g',?,?,?)", (role, text, now_iso()))
    conn.commit(); conn.close()
    messages = journal.recap_prompt("g")
    assert messages[0]["role"] == "system" and "harbour" in messages[1]["content"]


def test_recap_endpoint_saves_a_note_or_reports_failure(temp_db):
    from fastapi import HTTPException
    from backend.app.main import RecapIn, journal_recap

    conn = get_conn()
    for role, text in [("assistant", "You arrive."), ("user", "I wait.")]:
        conn.execute("INSERT INTO messages (session_id, role, content, created_at) VALUES ('g',?,?,?)", (role, text, now_iso()))
    conn.commit(); conn.close()

    with patch("core.chat_engine.send_to_llm", return_value="- You arrived at the harbour."):
        note = journal_recap(RecapIn(session_id="g"))["item"]
    assert note["kind"] == "recap" and "harbour" in note["body"]
    assert journal.list_notes("g", kind="recap")[0]["id"] == note["id"]

    with patch("core.chat_engine.send_to_llm", return_value="[LM Studio error] LM Studio isn't running — start its local server on port 1234."):
        with pytest.raises(HTTPException) as err:
            journal_recap(RecapIn(session_id="g"))
    assert err.value.status_code == 503 and "isn't running" in err.value.detail
    assert len(journal.list_notes("g", kind="recap")) == 1
