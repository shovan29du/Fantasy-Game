"""AiChat Pro v21 — DB Migration
Schema migration now runs inside storage.init_db() BEFORE module imports.
This module exists for backward compatibility and additional runtime checks."""
from core.storage import get_conn, _run_migrations

def migrate_db():
    """Run column migrations on existing database. Safe to call multiple times."""
    try:
        conn = get_conn()
        _run_migrations(conn)
        conn.close()
    except Exception as e:
        print(f"Migration note: {e}")
