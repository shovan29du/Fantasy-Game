"""Persistence layer for Ark_AI.

Supports SQLite (default, self-host friendly) and PostgreSQL (set
DATABASE_URL to switch). The two backends share the same call-site API:
`conn.execute(sql, params)` using `?` placeholders, returning a cursor with
dict-like rows (`row["col"]`). Schema is versioned and applied through the
migration list in migrations.py, so existing SQLite databases created by
earlier Ark_AI/Realzip/Relay versions upgrade in place without data loss.
"""
import os
import sqlite3
import time
import uuid

import migrations

APP_DIR = os.path.dirname(os.path.abspath(__file__))
_LEGACY_DB_PATH = os.path.join(APP_DIR, "realzip.db")
_DEFAULT_DB_PATH = _LEGACY_DB_PATH if os.path.exists(_LEGACY_DB_PATH) else os.path.join(APP_DIR, "ark_ai.db")
DB_PATH = os.environ.get("ARK_AI_DB_PATH", os.environ.get("RELAY_DB_PATH", _DEFAULT_DB_PATH))
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
BACKEND = "postgres" if DATABASE_URL else "sqlite"

_conn = None


class _PostgresConn:
    """Wraps a psycopg2 connection so call sites can use conn.execute(...)
    the same way sqlite3.Connection allows, with `?` placeholders and
    dict-like rows."""

    def __init__(self, raw):
        self._raw = raw

    def execute(self, sql, params=()):
        cur = self._raw.cursor()
        cur.execute(sql.replace("?", "%s"), params)
        return cur

    def executescript(self, sql):
        cur = self._raw.cursor()
        cur.execute(sql)

    def commit(self):
        self._raw.commit()

    def close(self):
        self._raw.close()


def get_conn():
    global _conn
    if _conn is None:
        if BACKEND == "postgres":
            import psycopg2
            import psycopg2.extras

            raw = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
            _conn = _PostgresConn(raw)
        else:
            _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            _conn.row_factory = sqlite3.Row
            _conn.execute("PRAGMA foreign_keys = ON")
    return _conn


def reset_conn():
    """Used by tests to point at a fresh database file/connection."""
    global _conn
    if _conn is not None:
        _conn.close()
    _conn = None


def insert_returning_id(table, columns, values, conn=None):
    """INSERT a row and return its new integer id, for either backend."""
    conn = conn or get_conn()
    placeholders = ", ".join("?" for _ in values)
    col_list = ", ".join(columns)
    if BACKEND == "postgres":
        cur = conn.execute(
            f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) RETURNING id", values
        )
        return cur.fetchone()["id"]
    cur = conn.execute(f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})", values)
    return cur.lastrowid


def init_db():
    conn = get_conn()
    migrations.run(conn, BACKEND)


# ---- users --------------------------------------------------------------
def create_user(username, password_hash):
    conn = get_conn()
    user_id = insert_returning_id(
        "users", ["username", "password_hash", "created_at"], (username, password_hash, time.time()), conn
    )
    conn.execute("INSERT INTO settings (user_id) VALUES (?)", (user_id,))
    conn.commit()
    return user_id


def get_user_by_username(username):
    conn = get_conn()
    return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def get_user_by_id(user_id):
    conn = get_conn()
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


# ---- settings -------------------------------------------------------------
def get_settings(user_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM settings WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        conn.execute("INSERT INTO settings (user_id) VALUES (?)", (user_id,))
        conn.commit()
        row = conn.execute("SELECT * FROM settings WHERE user_id = ?", (user_id,)).fetchone()
    return row


def update_settings(user_id, **fields):
    allowed = {"api_key", "ollama", "lm_studio", "system_prompt", "temperature", "anthropic_key", "deepseek_key",
               "openai_key", "gemini_key", "grok_key", "groq_key"}
    sets, vals = [], []
    for k, v in fields.items():
        if k in allowed:
            sets.append(f"{k} = ?")
            vals.append(v)
    if not sets:
        return
    conn = get_conn()
    conn.execute(f"UPDATE settings SET {', '.join(sets)} WHERE user_id = ?", (*vals, user_id))
    conn.commit()


# ---- conversations ---------------------------------------------------------
def create_project(user_id, name, description=""):
    conn = get_conn()
    project_id = uuid.uuid4().hex
    now = time.time()
    conn.execute(
        "INSERT INTO projects (id, user_id, name, description, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (project_id, user_id, name, description, now, now),
    )
    conn.commit()
    return project_id


def list_projects(user_id):
    conn = get_conn()
    return conn.execute(
        "SELECT id, name, description, created_at, updated_at FROM projects "
        "WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,),
    ).fetchall()


def get_project(project_id, user_id):
    if not project_id:
        return None
    conn = get_conn()
    return conn.execute(
        "SELECT * FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id)
    ).fetchone()


def update_project(project_id, user_id, name=None, description=None):
    fields, values = [], []
    if name is not None:
        fields.append("name = ?")
        values.append(name)
    if description is not None:
        fields.append("description = ?")
        values.append(description)
    if not fields:
        return False
    fields.append("updated_at = ?")
    values.append(time.time())
    conn = get_conn()
    cur = conn.execute(
        f"UPDATE projects SET {', '.join(fields)} WHERE id = ? AND user_id = ?",
        (*values, project_id, user_id),
    )
    conn.commit()
    return cur.rowcount > 0


def delete_project(project_id, user_id):
    conn = get_conn()
    conn.execute(
        "UPDATE conversations SET project_id = NULL WHERE project_id = ? AND user_id = ?",
        (project_id, user_id),
    )
    cur = conn.execute("DELETE FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id))
    conn.commit()
    return cur.rowcount > 0


def touch_project(project_id, user_id):
    if not project_id:
        return
    conn = get_conn()
    conn.execute("UPDATE projects SET updated_at = ? WHERE id = ? AND user_id = ?", (time.time(), project_id, user_id))
    conn.commit()


def create_conversation(user_id, title, model=None, branched_from=None, project_id=None):
    conn = get_conn()
    conv_id = uuid.uuid4().hex
    now = time.time()
    conn.execute(
        "INSERT INTO conversations (id, user_id, title, model, branched_from, project_id, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (conv_id, user_id, title, model, branched_from, project_id, now, now),
    )
    conn.commit()
    touch_project(project_id, user_id)
    return conv_id


def list_conversations(user_id):
    conn = get_conn()
    return conn.execute(
        "SELECT id, title, model, branched_from, project_id, created_at, updated_at FROM conversations "
        "WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,),
    ).fetchall()


def get_conversation(conversation_id, user_id):
    conn = get_conn()
    return conn.execute(
        "SELECT * FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id)
    ).fetchone()


def rename_conversation(conversation_id, user_id, title):
    conn = get_conn()
    conn.execute(
        "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ? AND user_id = ?",
        (title, time.time(), conversation_id, user_id),
    )
    conn.commit()


def touch_conversation(conversation_id, model=None):
    conn = get_conn()
    if model is not None:
        conn.execute(
            "UPDATE conversations SET updated_at = ?, model = ? WHERE id = ?",
            (time.time(), model, conversation_id),
        )
    else:
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (time.time(), conversation_id))
    conn.commit()


def delete_conversation(conversation_id, user_id):
    conn = get_conn()
    cur = conn.execute(
        "DELETE FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id)
    )
    conn.commit()
    return cur.rowcount > 0


# ---- messages ---------------------------------------------------------------
def add_message(conversation_id, role, content, model=None, relay_note=None):
    conn = get_conn()
    pos_row = conn.execute(
        "SELECT COALESCE(MAX(position), -1) + 1 AS next_pos FROM messages WHERE conversation_id = ?",
        (conversation_id,),
    ).fetchone()
    position = pos_row["next_pos"]
    conn.execute(
        "INSERT INTO messages (conversation_id, role, content, model, relay_note, position, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (conversation_id, role, content, model, relay_note, position, time.time()),
    )
    conn.commit()
    return position


def list_messages(conversation_id):
    conn = get_conn()
    return conn.execute(
        "SELECT role, content, model, relay_note, position, created_at FROM messages "
        "WHERE conversation_id = ? ORDER BY position ASC",
        (conversation_id,),
    ).fetchall()


def copy_messages_upto(source_id, dest_id, position):
    """Copy every message with position <= `position` from one conversation to another."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT role, content, model, relay_note FROM messages "
        "WHERE conversation_id = ? AND position <= ? ORDER BY position ASC",
        (source_id, position),
    ).fetchall()
    for row in rows:
        add_message(dest_id, row["role"], row["content"], model=row["model"], relay_note=row["relay_note"])


def truncate_messages_after(conversation_id, position):
    """Delete every message at or after `position` (used when editing a prior turn)."""
    conn = get_conn()
    conn.execute(
        "DELETE FROM messages WHERE conversation_id = ? AND position >= ?",
        (conversation_id, position),
    )
    conn.commit()


# ---- usage tracking ------------------------------------------------------------
def record_usage(user_id, conversation_id, model, chars, tokens_estimate):
    conn = get_conn()
    conn.execute(
        "INSERT INTO usage_events (user_id, conversation_id, model, chars, tokens_estimate, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, conversation_id, model, chars, tokens_estimate, time.time()),
    )
    conn.commit()


def daily_usage_summary(user_id, days=7):
    """Per-day message count / char / token totals for one user, most recent first."""
    conn = get_conn()
    cutoff = time.time() - days * 86400
    rows = conn.execute(
        "SELECT created_at, chars, tokens_estimate, model FROM usage_events "
        "WHERE user_id = ? AND created_at >= ? ORDER BY created_at ASC",
        (user_id, cutoff),
    ).fetchall()
    return _group_by_day(rows)


def _group_by_day(rows):
    buckets = {}
    for row in rows:
        day = time.strftime("%Y-%m-%d", time.gmtime(row["created_at"]))
        b = buckets.setdefault(day, {"day": day, "messages": 0, "chars": 0, "tokens": 0})
        b["messages"] += 1
        b["chars"] += row["chars"]
        b["tokens"] += row["tokens_estimate"]
    return [buckets[k] for k in sorted(buckets)]


# ---- persistent memory (facts recalled across conversations) ------------------
def list_memory(user_id):
    conn = get_conn()
    return conn.execute(
        "SELECT id, fact, created_at FROM memory_facts WHERE user_id = ? ORDER BY id ASC",
        (user_id,),
    ).fetchall()


def add_memory_facts(user_id, facts):
    conn = get_conn()
    now = time.time()
    for fact in facts:
        conn.execute(
            "INSERT INTO memory_facts (user_id, fact, created_at) VALUES (?, ?, ?)",
            (user_id, fact, now),
        )
    conn.commit()


def clear_memory(user_id):
    conn = get_conn()
    conn.execute("DELETE FROM memory_facts WHERE user_id = ?", (user_id,))
    conn.commit()
