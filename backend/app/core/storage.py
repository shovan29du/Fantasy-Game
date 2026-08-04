"""AiChat Pro — Core Storage
All tables. WAL mode. Table creation and column migrations run BEFORE any
module import, via init_db(), and are both idempotent."""
import json, sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from shared_config import DATA_DIR
from core.logging_setup import get_logger

log = get_logger(__name__)

DB_PATH = DATA_DIR / "aichat_pro.db"

# Bump whenever a new entry is added to _MIGRATIONS or _TABLES so the
# schema_version table reflects the schema the app expects.
SCHEMA_VERSION = 3

def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-2000")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn

def now_iso(): return datetime.now().isoformat()

def save_json(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

def load_json(path, default=None):
    p = Path(path)
    if not p.exists(): return default or {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        log.warning("Failed to parse JSON file %s; using default", p, exc_info=True)
        return default or {}


def get_bool_setting(key: str, default: bool = False) -> bool:
    """Read a user toggle from the settings table. Unset keys return `default`."""
    try:
        conn = get_conn()
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        conn.close()
        if row:
            return row["value"].strip().lower() in ("1", "true", "yes", "on")
    except Exception:
        log.warning("Failed to read bool setting %s; using default", key, exc_info=True)
    return default


def set_bool_setting(key: str, value: bool) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, "true" if value else "false"),
    )
    conn.commit()
    conn.close()


def get_setting(key: str, default: str = "") -> str:
    """Read a string setting from the settings table. Unset keys return `default`."""
    try:
        conn = get_conn()
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        conn.close()
        if row and row["value"] is not None:
            return row["value"]
    except Exception:
        log.warning("Failed to read setting %s; using default", key, exc_info=True)
    return default


def set_setting(key: str, value: str) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()

# ═══ FULL SCHEMA — runs once, idempotent ═══
_TABLES = [
    # Chat
    "CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT DEFAULT 'default', role TEXT NOT NULL, content TEXT NOT NULL, is_moment INTEGER DEFAULT 0, created_at TEXT NOT NULL)",
    # Characters
    "CREATE TABLE IF NOT EXISTS characters (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, age INTEGER, gender TEXT, race TEXT, species TEXT DEFAULT 'Humanoid', ethnicity TEXT, background TEXT, alignment TEXT DEFAULT 'Neutral', personality TEXT, skin TEXT, hair TEXT, eyes TEXT, body_type TEXT, height TEXT, facial_features TEXT, clothing_style TEXT, armor_style TEXT, accessories TEXT, measurements TEXT, looks INTEGER DEFAULT 5, charisma_stat INTEGER DEFAULT 10, strength INTEGER DEFAULT 10, dexterity INTEGER DEFAULT 10, intelligence INTEGER DEFAULT 10, wisdom INTEGER DEFAULT 10, constitution INTEGER DEFAULT 10, speed INTEGER DEFAULT 10, luck INTEGER DEFAULT 10, profession TEXT, weapon_training TEXT, magic_type TEXT, power_system TEXT, spells TEXT, skills TEXT, traits TEXT, backstory TEXT, scenario TEXT, goals TEXT, quirks TEXT, level INTEGER DEFAULT 1, xp INTEGER DEFAULT 0, photo_path TEXT, emotion_styles TEXT DEFAULT 'Friendly', identity_stability INTEGER DEFAULT 50, tags TEXT DEFAULT '[]', stat_points_available INTEGER DEFAULT 0, feats_json TEXT DEFAULT '[]', skill_tree_json TEXT DEFAULT '{}', profession_tier INTEGER DEFAULT 1, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS scenario_templates (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, scenario TEXT NOT NULL, created_at TEXT NOT NULL)",
    # Memory
    "CREATE TABLE IF NOT EXISTS memory_facts (id INTEGER PRIMARY KEY AUTOINCREMENT, fact TEXT NOT NULL, source TEXT, character_name TEXT, created_at TEXT NOT NULL)",
    # Relationships
    "CREATE TABLE IF NOT EXISTS relationships (character_name TEXT PRIMARY KEY, trust_score INTEGER DEFAULT 50, mood TEXT DEFAULT 'neutral', interaction_count INTEGER DEFAULT 0, bond_level TEXT DEFAULT 'acquaintance', loyalty INTEGER DEFAULT 50, reputation INTEGER DEFAULT 50, last_interaction_at TEXT)",
    "CREATE TABLE IF NOT EXISTS relationship_events (id INTEGER PRIMARY KEY AUTOINCREMENT, character_name TEXT NOT NULL, sentiment TEXT NOT NULL, trust_delta INTEGER NOT NULL, note TEXT, created_at TEXT NOT NULL)",
    # Quests
    "CREATE TABLE IF NOT EXISTS quests (id INTEGER PRIMARY KEY AUTOINCREMENT, character_name TEXT NOT NULL, quest_type TEXT NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL, reward TEXT NOT NULL, hint TEXT, progress INTEGER DEFAULT 0, status TEXT DEFAULT 'active', depends_on INTEGER, chain_id TEXT, created_at TEXT NOT NULL)",
    # Knowledge
    "CREATE TABLE IF NOT EXISTS knowledge_documents (id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT UNIQUE, title TEXT NOT NULL, content TEXT NOT NULL, embedding_json TEXT, indexed_at TEXT NOT NULL)",
    # Users
    "CREATE TABLE IF NOT EXISTS app_users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, security_q TEXT, security_a_hash TEXT, role TEXT DEFAULT 'user', created_at TEXT NOT NULL)",
    # Settings / Backups / Workflows
    "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS backups (id INTEGER PRIMARY KEY AUTOINCREMENT, archive_path TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS workflows (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, steps_json TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS personality_snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, character_id INTEGER NOT NULL, snapshot_json TEXT NOT NULL, created_at TEXT NOT NULL)",
    # World
    "CREATE TABLE IF NOT EXISTS worlds (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, magic_level TEXT DEFAULT 'medium', tech_level TEXT DEFAULT 'middle_age', space_alignment TEXT DEFAULT 'fantasy', world_json TEXT NOT NULL, world_tick INTEGER DEFAULT 0, weather TEXT DEFAULT 'clear', temperature TEXT DEFAULT 'mild', time_of_day TEXT DEFAULT 'morning', population INTEGER DEFAULT 1000, law_level INTEGER DEFAULT 50, crime_level INTEGER DEFAULT 10, treasury INTEGER DEFAULT 5000, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS world_locations (id INTEGER PRIMARY KEY AUTOINCREMENT, world_id INTEGER NOT NULL, name TEXT NOT NULL, loc_type TEXT NOT NULL, terrain TEXT, description TEXT, x INTEGER DEFAULT 0, y INTEGER DEFAULT 0, resources_json TEXT DEFAULT '{}', owner TEXT, population INTEGER DEFAULT 0)",
    "CREATE TABLE IF NOT EXISTS npcs (id INTEGER PRIMARY KEY AUTOINCREMENT, world_id INTEGER, name TEXT NOT NULL, age INTEGER, profession TEXT, personality TEXT, skills TEXT, alignment TEXT DEFAULT 'Neutral', faction TEXT, location_id INTEGER, mood TEXT DEFAULT 'neutral', schedule_json TEXT DEFAULT '{}', details_json TEXT, goal_survive INTEGER DEFAULT 5, goal_profit INTEGER DEFAULT 5, goal_loyalty INTEGER DEFAULT 5, memory_json TEXT DEFAULT '[]', created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS factions (id INTEGER PRIMARY KEY AUTOINCREMENT, world_id INTEGER, name TEXT NOT NULL, alignment TEXT DEFAULT 'Neutral', reputation INTEGER DEFAULT 50, leader TEXT, members_json TEXT DEFAULT '[]', territory TEXT, treasury INTEGER DEFAULT 1000, military_strength INTEGER DEFAULT 100, relations_json TEXT DEFAULT '{}', details_json TEXT DEFAULT '{}', created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS dungeons (id INTEGER PRIMARY KEY AUTOINCREMENT, world_id INTEGER, name TEXT NOT NULL, dungeon_type TEXT DEFAULT 'random', levels INTEGER DEFAULT 1, rooms_json TEXT NOT NULL, created_at TEXT NOT NULL)",
    # Economy
    "CREATE TABLE IF NOT EXISTS economy (character_id INTEGER PRIMARY KEY, gold INTEGER DEFAULT 0, credits INTEGER DEFAULT 0, tokens INTEGER DEFAULT 0, assets_json TEXT DEFAULT '[]', inventory_json TEXT DEFAULT '[]')",
    "CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, character_id INTEGER NOT NULL, tx_type TEXT NOT NULL, amount INTEGER NOT NULL, currency TEXT DEFAULT 'gold', reason TEXT, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS market_prices (id INTEGER PRIMARY KEY AUTOINCREMENT, world_id INTEGER, item TEXT NOT NULL, supply INTEGER DEFAULT 100, demand INTEGER DEFAULT 100, base_price REAL DEFAULT 10.0, current_price REAL DEFAULT 10.0, updated_at TEXT)",
    # Combat
    "CREATE TABLE IF NOT EXISTS combat_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, world_id INTEGER, attacker TEXT NOT NULL, defender TEXT NOT NULL, result_json TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS combat_state (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, unit_name TEXT NOT NULL, unit_type TEXT DEFAULT 'player', hp INTEGER DEFAULT 100, max_hp INTEGER DEFAULT 100, x INTEGER DEFAULT 0, y INTEGER DEFAULT 0, status_effects TEXT DEFAULT '[]', initiative INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1)",
    # Campaign / Timeline
    "CREATE TABLE IF NOT EXISTS campaign_events (id INTEGER PRIMARY KEY AUTOINCREMENT, world_id INTEGER, event_type TEXT NOT NULL, description TEXT NOT NULL, tick INTEGER DEFAULT 0, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS campaign_saves (id INTEGER PRIMARY KEY AUTOINCREMENT, world_id INTEGER NOT NULL, save_name TEXT NOT NULL, save_json TEXT NOT NULL, created_at TEXT NOT NULL)",
    # Skill trees
    "CREATE TABLE IF NOT EXISTS skill_trees (id INTEGER PRIMARY KEY AUTOINCREMENT, character_id INTEGER NOT NULL, tree_json TEXT NOT NULL, created_at TEXT NOT NULL)",
    # Inventory
    "CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, character_id INTEGER NOT NULL, item_name TEXT NOT NULL, item_type TEXT DEFAULT 'misc', quantity INTEGER DEFAULT 1, value INTEGER DEFAULT 0, description TEXT DEFAULT '', equip_slot TEXT, stat_bonuses TEXT DEFAULT '{}', source TEXT DEFAULT 'manual', created_at TEXT NOT NULL)",
    # Assets
    "CREATE TABLE IF NOT EXISTS character_assets (id INTEGER PRIMARY KEY AUTOINCREMENT, character_id INTEGER NOT NULL, asset_type TEXT NOT NULL, asset_name TEXT NOT NULL, value INTEGER DEFAULT 0, details_json TEXT DEFAULT '{}', created_at TEXT NOT NULL)",
    # Media
    "CREATE TABLE IF NOT EXISTS media_items (id INTEGER PRIMARY KEY AUTOINCREMENT, character_id INTEGER, character_name TEXT DEFAULT 'Unassigned', media_type TEXT NOT NULL, title TEXT NOT NULL, description TEXT, file_path TEXT, tags TEXT DEFAULT '[]', source TEXT DEFAULT 'upload', created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS achievements (id INTEGER PRIMARY KEY AUTOINCREMENT, character_id INTEGER, character_name TEXT DEFAULT 'Unassigned', title TEXT NOT NULL, description TEXT, badge_icon TEXT DEFAULT '🏆', bonus_stat TEXT, bonus_value INTEGER DEFAULT 0, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS memory_snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, character_id INTEGER, character_name TEXT DEFAULT 'Unassigned', title TEXT NOT NULL, content TEXT, emotion TEXT, created_at TEXT NOT NULL)",
    # NPC schedules
    "CREATE TABLE IF NOT EXISTS npc_schedules (id INTEGER PRIMARY KEY AUTOINCREMENT, npc_id INTEGER NOT NULL, world_id INTEGER, time_slot TEXT NOT NULL, activity TEXT NOT NULL, location TEXT, mood TEXT DEFAULT 'neutral')",
    # Weather
    "CREATE TABLE IF NOT EXISTS world_weather_log (id INTEGER PRIMARY KEY AUTOINCREMENT, world_id INTEGER NOT NULL, tick INTEGER DEFAULT 0, weather TEXT NOT NULL, temperature TEXT, effects TEXT DEFAULT '[]', travel_blocked INTEGER DEFAULT 0, food_modifier REAL DEFAULT 1.0, army_modifier REAL DEFAULT 1.0, created_at TEXT NOT NULL)",
    # Resources
    "CREATE TABLE IF NOT EXISTS world_resources (id INTEGER PRIMARY KEY AUTOINCREMENT, world_id INTEGER NOT NULL, location_id INTEGER, resource_type TEXT NOT NULL, quantity INTEGER DEFAULT 100, production_rate INTEGER DEFAULT 5)",
    # Diplomacy
    "CREATE TABLE IF NOT EXISTS diplomacy (id INTEGER PRIMARY KEY AUTOINCREMENT, world_id INTEGER NOT NULL, faction_a TEXT NOT NULL, faction_b TEXT NOT NULL, relation TEXT DEFAULT 'neutral', trade_active INTEGER DEFAULT 0, treaty TEXT, created_at TEXT NOT NULL)",
    # Laws
    "CREATE TABLE IF NOT EXISTS world_laws (id INTEGER PRIMARY KEY AUTOINCREMENT, world_id INTEGER NOT NULL, law_name TEXT NOT NULL, description TEXT, penalty TEXT, active INTEGER DEFAULT 1)",
    # Random events
    "CREATE TABLE IF NOT EXISTS random_events (id INTEGER PRIMARY KEY AUTOINCREMENT, world_id INTEGER, event_text TEXT NOT NULL, impact_json TEXT DEFAULT '{}', tick INTEGER DEFAULT 0, created_at TEXT NOT NULL)",
    # Chat saves
    "CREATE TABLE IF NOT EXISTS chat_saves (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, save_name TEXT, character_name TEXT, created_at TEXT)",
    # Faction wars
    "CREATE TABLE IF NOT EXISTS faction_wars (id INTEGER PRIMARY KEY AUTOINCREMENT, world_id INTEGER, attacker TEXT NOT NULL, defender TEXT NOT NULL, attacker_strength INTEGER, defender_strength INTEGER, result TEXT, territory_changed TEXT, tick INTEGER, created_at TEXT NOT NULL)",
    # AI director
    "CREATE TABLE IF NOT EXISTS ai_director (id INTEGER PRIMARY KEY AUTOINCREMENT, world_id INTEGER, difficulty_level INTEGER DEFAULT 5, threat_level INTEGER DEFAULT 50, player_power INTEGER DEFAULT 10, last_adjusted TEXT)",
    # Media jobs
    "CREATE TABLE IF NOT EXISTS media_jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, job_type TEXT NOT NULL, status TEXT DEFAULT 'queued', input_path TEXT, output_path TEXT, params_json TEXT DEFAULT '{}', created_at TEXT NOT NULL, completed_at TEXT)",
]

# Column additions for existing tables that may need upgrading
_MIGRATIONS = [
    ("characters", "tags", "TEXT DEFAULT '[]'"),
    ("characters", "stat_points_available", "INTEGER DEFAULT 0"),
    ("characters", "feats_json", "TEXT DEFAULT '[]'"),
    ("characters", "skill_tree_json", "TEXT DEFAULT '{}'"),
    ("characters", "profession_tier", "INTEGER DEFAULT 1"),
    ("characters", "skill_points_available", "INTEGER DEFAULT 0"),
    ("characters", "other_points_available", "INTEGER DEFAULT 0"),
    ("npcs", "goal_survive", "INTEGER DEFAULT 5"),
    ("npcs", "goal_profit", "INTEGER DEFAULT 5"),
    ("npcs", "goal_loyalty", "INTEGER DEFAULT 5"),
    ("npcs", "memory_json", "TEXT DEFAULT '[]'"),
    ("factions", "military_strength", "INTEGER DEFAULT 100"),
    ("quests", "depends_on", "INTEGER"),
    ("quests", "chain_id", "TEXT"),
    ("achievements", "bonus_stat", "TEXT"),
    ("achievements", "bonus_value", "INTEGER DEFAULT 0"),
    ("inventory", "equip_slot", "TEXT"),
    ("inventory", "stat_bonuses", "TEXT DEFAULT '{}'"),
    ("combat_state", "status_effects", "TEXT DEFAULT '[]'"),
    ("combat_state", "initiative", "INTEGER DEFAULT 0"),
    ("world_weather_log", "travel_blocked", "INTEGER DEFAULT 0"),
    ("world_weather_log", "food_modifier", "REAL DEFAULT 1.0"),
    ("world_weather_log", "army_modifier", "REAL DEFAULT 1.0"),
    # Multiverse system: reality signature + power tier per character, and
    # 0-10 world-scale ratings + reality type per world (see
    # backend.app.domain.worldscale / domain.multiverse).
    ("characters", "reality_signature", "TEXT DEFAULT '{}'"),
    ("characters", "power_tier", "INTEGER DEFAULT 2"),
    ("worlds", "ratings_json", "TEXT DEFAULT '{}'"),
    ("worlds", "reality_type", "TEXT DEFAULT 'Prime Reality'"),
]

def _create_tables(conn):
    """Create all tables that don't already exist. Pure CREATE TABLE IF NOT EXISTS,
    so this is always safe to re-run."""
    cur = conn.cursor()
    for stmt in _TABLES:
        try:
            cur.execute(stmt)
        except sqlite3.OperationalError:
            log.warning("Table creation statement failed: %s", stmt[:80], exc_info=True)
    conn.commit()


def _is_duplicate_column_error(exc: sqlite3.OperationalError) -> bool:
    return "duplicate column name" in str(exc).lower()


def _run_migrations(conn):
    """Add missing columns to existing tables. Idempotent: a column that
    already exists is silently skipped, any other failure is logged (not
    swallowed) so real migration problems are visible."""
    cur = conn.cursor()
    for table, col, col_def in _MIGRATIONS:
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError as e:
            if not _is_duplicate_column_error(e):
                log.error("Migration failed for %s.%s: %s", table, col, e)
    conn.commit()


def _record_schema_version(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (id INTEGER PRIMARY KEY CHECK (id = 1), "
        "version INTEGER NOT NULL, applied_at TEXT NOT NULL)"
    )
    conn.execute(
        "INSERT INTO schema_version (id, version, applied_at) VALUES (1, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET version=excluded.version, applied_at=excluded.applied_at",
        (SCHEMA_VERSION, now_iso()),
    )
    conn.commit()


def get_schema_version(conn=None) -> int:
    """Return the schema version currently recorded in the database, or 0 if unset."""
    own_conn = conn is None
    if own_conn:
        conn = get_conn()
    try:
        row = conn.execute(
            "SELECT version FROM schema_version WHERE id=1"
        ).fetchone()
        return row["version"] if row else 0
    except sqlite3.OperationalError:
        return 0
    finally:
        if own_conn:
            conn.close()


def init_db():
    """Create all tables + run column migrations. Called BEFORE any module
    import, deterministically, on every startup. Safe to call repeatedly."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    _create_tables(conn)
    _run_migrations(conn)
    _record_schema_version(conn)
    conn.close()


# ═══ Cascading delete ═══
# The schema has no foreign keys (tables are soft-linked by id/name), so
# deleting a character or world leaves orphaned rows behind unless every
# related table is cleaned up explicitly here in one place.

_CHARACTER_ID_TABLES = [
    "economy", "transactions", "inventory", "character_assets",
    "media_items", "achievements", "memory_snapshots",
    "personality_snapshots", "skill_trees",
]
_CHARACTER_NAME_TABLES = [
    "relationships", "relationship_events", "quests", "memory_facts",
]
_WORLD_ID_TABLES = [
    "world_locations", "npcs", "factions", "dungeons", "market_prices",
    "combat_logs", "campaign_events", "campaign_saves", "npc_schedules",
    "world_weather_log", "world_resources", "diplomacy", "world_laws",
    "random_events", "faction_wars", "ai_director",
]


def delete_character(character_id: int) -> bool:
    """Delete a character and every row that references it, in one transaction."""
    conn = get_conn()
    try:
        row = conn.execute("SELECT name FROM characters WHERE id=?", (character_id,)).fetchone()
        if not row:
            return False
        name = row["name"]
        for tbl in _CHARACTER_ID_TABLES:
            conn.execute(f"DELETE FROM {tbl} WHERE character_id=?", (character_id,))
        if name:
            for tbl in _CHARACTER_NAME_TABLES:
                conn.execute(f"DELETE FROM {tbl} WHERE character_name=?", (name,))
        conn.execute("DELETE FROM characters WHERE id=?", (character_id,))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        log.exception("delete_character failed for id=%s", character_id)
        raise
    finally:
        conn.close()


def delete_world(world_id: int) -> bool:
    """Delete a world and every row that references it, in one transaction."""
    conn = get_conn()
    try:
        row = conn.execute("SELECT id FROM worlds WHERE id=?", (world_id,)).fetchone()
        if not row:
            return False
        for tbl in _WORLD_ID_TABLES:
            conn.execute(f"DELETE FROM {tbl} WHERE world_id=?", (world_id,))
        conn.execute("DELETE FROM worlds WHERE id=?", (world_id,))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        log.exception("delete_world failed for id=%s", world_id)
        raise
    finally:
        conn.close()

# MemOS-inspired memory columns
_MIGRATIONS.append(("memory_facts", "memory_type", "TEXT DEFAULT 'general'"))
_MIGRATIONS.append(("memory_facts", "importance", "REAL DEFAULT 0.5"))
_MIGRATIONS.append(("memory_facts", "confidence", "REAL DEFAULT 1.0"))
_MIGRATIONS.append(("memory_facts", "entities_json", "TEXT DEFAULT '[]'"))
_MIGRATIONS.append(("memory_facts", "tags", "TEXT DEFAULT '[]'"))
_MIGRATIONS.append(("memory_facts", "access_count", "INTEGER DEFAULT 0"))
_MIGRATIONS.append(("memory_facts", "last_accessed", "TEXT"))
_MIGRATIONS.append(("memory_facts", "character_name", "TEXT"))

# Memory graph table
_TABLES.append("""CREATE TABLE IF NOT EXISTS memory_graph (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_entity TEXT NOT NULL,
    target_entity TEXT NOT NULL,
    relation_type TEXT DEFAULT 'related_to',
    weight REAL DEFAULT 1.0,
    created_at TEXT NOT NULL
)""")

# Lorebook table (from Backyard.ai)
_TABLES.append("""CREATE TABLE IF NOT EXISTS lorebook (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    keywords_json TEXT DEFAULT '[]',
    world_id INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 0,
    always_active INTEGER DEFAULT 0,
    case_sensitive INTEGER DEFAULT 0,
    enabled INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
)""")
