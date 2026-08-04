"""Database initialization, idempotency, and message CRUD."""
import sqlite3

import core.storage as storage


def test_init_db_creates_expected_tables(temp_db):
    conn = sqlite3.connect(str(temp_db))
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    conn.close()
    for expected in ("messages", "characters", "app_users", "settings",
                      "worlds", "schema_version", "lorebook", "memory_graph"):
        assert expected in tables


def test_init_db_is_idempotent(temp_db):
    # Calling init_db repeatedly must not raise and must not duplicate data.
    storage.init_db()
    storage.init_db()
    conn = storage.get_conn()
    version = storage.get_schema_version(conn)
    conn.close()
    assert version == storage.SCHEMA_VERSION


def test_migration_skips_duplicate_column_silently(temp_db):
    # Re-running the column migrations against an already-migrated DB
    # must not raise, since ADD COLUMN on an existing column is expected.
    conn = storage.get_conn()
    storage._run_migrations(conn)
    conn.close()


def test_message_crud(temp_db):
    conn = storage.get_conn()
    conn.execute(
        "INSERT INTO messages (session_id, role, content, created_at) VALUES (?,?,?,?)",
        ("s1", "user", "hello", storage.now_iso()),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM messages WHERE session_id='s1'").fetchone()
    assert row["content"] == "hello"

    msg_id = row["id"]
    conn.execute("UPDATE messages SET content=? WHERE id=?", ("edited", msg_id))
    conn.commit()
    row = conn.execute("SELECT content FROM messages WHERE id=?", (msg_id,)).fetchone()
    assert row["content"] == "edited"

    conn.execute("DELETE FROM messages WHERE id=?", (msg_id,))
    conn.commit()
    row = conn.execute("SELECT * FROM messages WHERE session_id='s1'").fetchone()
    assert row is None
    conn.close()


def test_settings_crud(temp_db):
    conn = storage.get_conn()
    conn.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ("foo", "bar"))
    conn.commit()
    row = conn.execute("SELECT value FROM settings WHERE key='foo'").fetchone()
    assert row["value"] == "bar"

    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        ("foo", "baz"),
    )
    conn.commit()
    row = conn.execute("SELECT value FROM settings WHERE key='foo'").fetchone()
    assert row["value"] == "baz"
    conn.close()
