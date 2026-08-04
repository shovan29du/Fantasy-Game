"""Versioned schema migrations for Ark_AI.

Each migration is a (version, description, sqlite_sql, postgres_sql) tuple.
Applied migrations are recorded in `schema_version`, so `run()` is idempotent:
calling it again (e.g. on every app start) only applies what's missing. This
also means an existing SQLite database created by an earlier Ark_AI/Realzip
release upgrades in place — migration 1 uses CREATE TABLE IF NOT EXISTS so it
is a no-op against a database that already has those tables, and later
migrations add the new columns/tables that release didn't have yet.
"""
import time

SCHEMA_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at REAL NOT NULL
);
"""

MIGRATIONS = [
    (
        1,
        "initial schema: users, settings, conversations, messages",
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS settings (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            api_key TEXT NOT NULL DEFAULT '',
            ollama TEXT NOT NULL DEFAULT '',
            system_prompt TEXT NOT NULL DEFAULT '',
            temperature REAL NOT NULL DEFAULT 0.7
        );
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL DEFAULT 'Untitled',
            model TEXT,
            branched_from TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            model TEXT,
            relay_note TEXT,
            position INTEGER NOT NULL,
            created_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
        CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
        """,
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at DOUBLE PRECISION NOT NULL
        );
        CREATE TABLE IF NOT EXISTS settings (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            api_key TEXT NOT NULL DEFAULT '',
            ollama TEXT NOT NULL DEFAULT '',
            system_prompt TEXT NOT NULL DEFAULT '',
            temperature DOUBLE PRECISION NOT NULL DEFAULT 0.7
        );
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL DEFAULT 'Untitled',
            model TEXT,
            branched_from TEXT,
            created_at DOUBLE PRECISION NOT NULL,
            updated_at DOUBLE PRECISION NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            model TEXT,
            relay_note TEXT,
            position INTEGER NOT NULL,
            created_at DOUBLE PRECISION NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
        CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
        """,
    ),
    (
        2,
        "password reset tokens",
        """
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token TEXT NOT NULL UNIQUE,
            created_at REAL NOT NULL,
            expires_at REAL NOT NULL,
            used INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_reset_tokens_user ON password_reset_tokens(user_id);
        """,
        """
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token TEXT NOT NULL UNIQUE,
            created_at DOUBLE PRECISION NOT NULL,
            expires_at DOUBLE PRECISION NOT NULL,
            used INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_reset_tokens_user ON password_reset_tokens(user_id);
        """,
    ),
    (
        3,
        "admin role on users",
        "ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0;",
        "ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0;",
    ),
    (
        4,
        "usage tracking events",
        """
        CREATE TABLE IF NOT EXISTS usage_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            conversation_id TEXT,
            model TEXT,
            chars INTEGER NOT NULL DEFAULT 0,
            tokens_estimate INTEGER NOT NULL DEFAULT 0,
            created_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_usage_user ON usage_events(user_id);
        CREATE INDEX IF NOT EXISTS idx_usage_created ON usage_events(created_at);
        """,
        """
        CREATE TABLE IF NOT EXISTS usage_events (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            conversation_id TEXT,
            model TEXT,
            chars INTEGER NOT NULL DEFAULT 0,
            tokens_estimate INTEGER NOT NULL DEFAULT 0,
            created_at DOUBLE PRECISION NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_usage_user ON usage_events(user_id);
        CREATE INDEX IF NOT EXISTS idx_usage_created ON usage_events(created_at);
        """,
    ),
    (
        5,
        "persistent memory facts",
        """
        CREATE TABLE IF NOT EXISTS memory_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            fact TEXT NOT NULL,
            created_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_memory_user ON memory_facts(user_id);
        """,
        """
        CREATE TABLE IF NOT EXISTS memory_facts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            fact TEXT NOT NULL,
            created_at DOUBLE PRECISION NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_memory_user ON memory_facts(user_id);
        """,
    ),
    (
        6,
        "direct Anthropic (Claude) and DeepSeek API keys",
        """
        ALTER TABLE settings ADD COLUMN anthropic_key TEXT NOT NULL DEFAULT '';
        ALTER TABLE settings ADD COLUMN deepseek_key TEXT NOT NULL DEFAULT '';
        """,
        """
        ALTER TABLE settings ADD COLUMN anthropic_key TEXT NOT NULL DEFAULT '';
        ALTER TABLE settings ADD COLUMN deepseek_key TEXT NOT NULL DEFAULT '';
        """,
    ),
    (
        7,
        "direct OpenAI (ChatGPT) and Google Gemini API keys",
        """
        ALTER TABLE settings ADD COLUMN openai_key TEXT NOT NULL DEFAULT '';
        ALTER TABLE settings ADD COLUMN gemini_key TEXT NOT NULL DEFAULT '';
        """,
        """
        ALTER TABLE settings ADD COLUMN openai_key TEXT NOT NULL DEFAULT '';
        ALTER TABLE settings ADD COLUMN gemini_key TEXT NOT NULL DEFAULT '';
        """,
    ),
    (
        8,
        "direct xAI (Grok) API key",
        """
        ALTER TABLE settings ADD COLUMN grok_key TEXT NOT NULL DEFAULT '';
        """,
        """
        ALTER TABLE settings ADD COLUMN grok_key TEXT NOT NULL DEFAULT '';
        """,
    ),
    (
        9,
        "direct Groq Cloud (free-tier) API key",
        """
        ALTER TABLE settings ADD COLUMN groq_key TEXT NOT NULL DEFAULT '';
        """,
        """
        ALTER TABLE settings ADD COLUMN groq_key TEXT NOT NULL DEFAULT '';
        """,
    ),
    (
        10,
        "projects workspace",
        """
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id);
        ALTER TABLE conversations ADD COLUMN project_id TEXT;
        """,
        """
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            created_at DOUBLE PRECISION NOT NULL,
            updated_at DOUBLE PRECISION NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id);
        ALTER TABLE conversations ADD COLUMN project_id TEXT;
        """,
    ),
    (
        11,
        "LM Studio local server URL",
        """
        ALTER TABLE settings ADD COLUMN lm_studio TEXT NOT NULL DEFAULT 'http://localhost:1234';
        """,
        """
        ALTER TABLE settings ADD COLUMN lm_studio TEXT NOT NULL DEFAULT 'http://localhost:1234';
        """,
    ),
    (
        12,
        "additional provider API keys: Mistral, Together.ai, Perplexity, Fireworks",
        """
        ALTER TABLE settings ADD COLUMN mistral_key TEXT NOT NULL DEFAULT '';
        ALTER TABLE settings ADD COLUMN together_key TEXT NOT NULL DEFAULT '';
        ALTER TABLE settings ADD COLUMN perplexity_key TEXT NOT NULL DEFAULT '';
        ALTER TABLE settings ADD COLUMN fireworks_key TEXT NOT NULL DEFAULT '';
        """,
        """
        ALTER TABLE settings ADD COLUMN mistral_key TEXT NOT NULL DEFAULT '';
        ALTER TABLE settings ADD COLUMN together_key TEXT NOT NULL DEFAULT '';
        ALTER TABLE settings ADD COLUMN perplexity_key TEXT NOT NULL DEFAULT '';
        ALTER TABLE settings ADD COLUMN fireworks_key TEXT NOT NULL DEFAULT '';
        """,
    ),

]


def applied_versions(conn):
    conn.executescript(SCHEMA_VERSION_TABLE) if hasattr(conn, "executescript") else None
    conn.commit()
    rows = conn.execute("SELECT version FROM schema_version").fetchall()
    return {r["version"] for r in rows}


def run(conn, backend):
    """Apply every migration that hasn't been recorded yet, in order. Safe to
    call on every app start — already-applied migrations are skipped."""
    done = applied_versions(conn)
    for version, description, sqlite_sql, postgres_sql in MIGRATIONS:
        if version in done:
            continue
        sql = postgres_sql if backend == "postgres" else sqlite_sql
        try:
            conn.executescript(sql)
        except Exception:
            # Re-running an ALTER TABLE ... ADD COLUMN against a database
            # that already has the column (e.g. a half-applied migration
            # retried after a crash) should not be fatal.
            conn.commit()
        conn.execute(
            "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
            (version, time.time()),
        )
        conn.commit()