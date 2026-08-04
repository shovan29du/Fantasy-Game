"""Cascading delete for characters and worlds (core/storage.py).

The schema has no foreign keys, so delete_character/delete_world must clean
up every table that references the deleted row by hand.
"""
from core.storage import get_conn, now_iso, delete_character, delete_world


def _make_character(conn, name="Aria"):
    cur = conn.execute(
        "INSERT INTO characters (name, created_at) VALUES (?, ?)", (name, now_iso())
    )
    return cur.lastrowid


def test_delete_character_removes_id_and_name_linked_rows(temp_db):
    conn = get_conn()
    cid = _make_character(conn, "Aria")
    conn.execute("INSERT INTO inventory (character_id, item_name, created_at) VALUES (?, ?, ?)",
                 (cid, "Sword", now_iso()))
    conn.execute("INSERT INTO economy (character_id, gold) VALUES (?, ?)", (cid, 100))
    conn.execute("INSERT INTO relationships (character_name, trust_score) VALUES (?, ?)",
                 ("Aria", 50))
    conn.execute("INSERT INTO quests (character_name, quest_type, title, description, reward, created_at) "
                 "VALUES (?,?,?,?,?,?)", ("Aria", "story", "Find the sword", "desc", "50 gold", now_iso()))
    conn.execute("INSERT INTO memory_facts (fact, character_name, created_at) VALUES (?, ?, ?)",
                 ("Aria loves tea", "Aria", now_iso()))
    conn.commit()
    conn.close()

    assert delete_character(cid) is True

    conn = get_conn()
    assert conn.execute("SELECT * FROM characters WHERE id=?", (cid,)).fetchone() is None
    assert conn.execute("SELECT * FROM inventory WHERE character_id=?", (cid,)).fetchone() is None
    assert conn.execute("SELECT * FROM economy WHERE character_id=?", (cid,)).fetchone() is None
    assert conn.execute("SELECT * FROM relationships WHERE character_name='Aria'").fetchone() is None
    assert conn.execute("SELECT * FROM quests WHERE character_name='Aria'").fetchone() is None
    assert conn.execute("SELECT * FROM memory_facts WHERE character_name='Aria'").fetchone() is None
    conn.close()


def test_delete_character_does_not_touch_other_characters(temp_db):
    conn = get_conn()
    keep_id = _make_character(conn, "Kept")
    doomed_id = _make_character(conn, "Doomed")
    conn.execute("INSERT INTO inventory (character_id, item_name, created_at) VALUES (?, ?, ?)",
                 (keep_id, "Shield", now_iso()))
    conn.execute("INSERT INTO relationships (character_name, trust_score) VALUES (?, ?)", ("Kept", 60))
    conn.commit()
    conn.close()

    delete_character(doomed_id)

    conn = get_conn()
    assert conn.execute("SELECT * FROM characters WHERE id=?", (keep_id,)).fetchone() is not None
    assert conn.execute("SELECT * FROM inventory WHERE character_id=?", (keep_id,)).fetchone() is not None
    assert conn.execute("SELECT * FROM relationships WHERE character_name='Kept'").fetchone() is not None
    conn.close()


def test_delete_character_returns_false_for_unknown_id(temp_db):
    assert delete_character(999999) is False


def test_delete_world_removes_linked_rows(temp_db):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO worlds (name, world_json, created_at) VALUES (?, ?, ?)",
        ("Testland", "{}", now_iso()),
    )
    wid = cur.lastrowid
    conn.execute("INSERT INTO npcs (world_id, name, created_at) VALUES (?, ?, ?)", (wid, "Bob", now_iso()))
    conn.execute("INSERT INTO factions (world_id, name, created_at) VALUES (?, ?, ?)", (wid, "Guild", now_iso()))
    conn.execute("INSERT INTO campaign_events (world_id, event_type, description, created_at) VALUES (?,?,?,?)",
                 (wid, "test", "something happened", now_iso()))
    conn.commit()
    conn.close()

    assert delete_world(wid) is True

    conn = get_conn()
    assert conn.execute("SELECT * FROM worlds WHERE id=?", (wid,)).fetchone() is None
    assert conn.execute("SELECT * FROM npcs WHERE world_id=?", (wid,)).fetchone() is None
    assert conn.execute("SELECT * FROM factions WHERE world_id=?", (wid,)).fetchone() is None
    assert conn.execute("SELECT * FROM campaign_events WHERE world_id=?", (wid,)).fetchone() is None
    conn.close()


def test_delete_world_returns_false_for_unknown_id(temp_db):
    assert delete_world(999999) is False
