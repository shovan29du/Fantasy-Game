"""AiChat Pro v21 — Relationship + Trust Engine
Tags affect initial trust. Trust decays/grows over time without interaction.
Tracks trust (0-100), mood, bond level, loyalty, reputation per character."""

from __future__ import annotations
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from core.storage import get_conn, now_iso
from core.logging_setup import get_logger

log = get_logger(__name__)

BOND_LEVELS = ["stranger", "acquaintance", "friend", "close_friend", "trusted_ally", "soulbound"]
MOODS = ["hostile", "annoyed", "neutral", "pleasant", "happy", "elated"]

# Tag → initial trust score overrides
TAG_TRUST_MAP = {
    "Girlfriend": 70, "Boyfriend": 70, "Wife": 85, "Husband": 85,
    "Lover": 75, "Romance": 60, "Best Friend": 65, "Friend": 55,
    "Ally": 60, "Companion": 55, "Partner": 65, "Protector": 60,
    "Mentor": 55, "Student": 50, "Servant": 45, "Master": 40,
    "Rival": 25, "Enemy": 15, "Nemesis": 5, "Stalker": 20,
    "Bully": 20, "Yandere": 35, "Tsundere": 30, "Kuudere": 35,
    "Step-Mom": 45, "Step-Dad": 45, "Step-Sister": 45, "Step-Brother": 45,
    "Dominant": 40, "Submissive": 40, "Pet": 50, "Owner": 40,
    "Seductive": 35, "Flirty": 40, "Innocent": 55, "Dark": 30,
    "Evil": 15, "Hero": 60, "Villain": 20, "Anti-Hero": 35,
    "Royalty": 45, "Noble": 45, "Commoner": 50, "Outcast": 30,
}

# Trust decay/growth per day without interaction
DECAY_RATE = -1  # lose 1 trust per day of no interaction
GROWTH_RATE = 0.5  # gain 0.5 trust per day for high-bond characters

def _bond_from_trust(trust: int) -> str:
    if trust >= 90: return "soulbound"
    if trust >= 75: return "trusted_ally"
    if trust >= 55: return "close_friend"
    if trust >= 35: return "friend"
    if trust >= 15: return "acquaintance"
    return "stranger"

def _mood_from_trust(trust: int) -> str:
    if trust >= 80: return "elated"
    if trust >= 60: return "happy"
    if trust >= 40: return "pleasant"
    if trust >= 20: return "neutral"
    if trust >= 10: return "annoyed"
    return "hostile"

def trust_from_tags(tags) -> int:
    """Calculate initial trust from character tags."""
    if isinstance(tags, str):
        try: tags = json.loads(tags)
        except Exception:
            log.debug("suppressed error", exc_info=True)
            tags = [t.strip() for t in tags.split(",") if t.strip()]
    if not tags:
        return 50
    scores = [TAG_TRUST_MAP[t] for t in tags if t in TAG_TRUST_MAP]
    if not scores:
        return 50
    return int(sum(scores) / len(scores))

def get_relationship(character_name: str) -> Optional[Dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM relationships WHERE character_name=?",
                       (character_name,)).fetchone()
    conn.close()
    return dict(row) if row else None

def ensure_relationship(character_name: str, tags=None) -> Dict:
    """Create or get relationship. If tags provided, use for initial trust."""
    rel = get_relationship(character_name)
    if rel:
        return rel
    initial_trust = trust_from_tags(tags) if tags else 50
    mood = _mood_from_trust(initial_trust)
    bond = _bond_from_trust(initial_trust)
    conn = get_conn()
    conn.execute(
        "INSERT INTO relationships (character_name, trust_score, mood, interaction_count, "
        "bond_level, loyalty, reputation, last_interaction_at) VALUES (?,?,?,?,?,?,?,?)",
        (character_name, initial_trust, mood, 0, bond, 50, 50, now_iso()))
    conn.commit()
    conn.close()
    return get_relationship(character_name)

def apply_time_decay():
    """Apply trust decay/growth based on time since last interaction. Call on app load."""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM relationships").fetchall()
    now = datetime.now()
    for row in rows:
        last = row["last_interaction_at"]
        if not last:
            continue
        try:
            last_dt = datetime.fromisoformat(last)
        except Exception:
            log.debug("suppressed error", exc_info=True)
            continue
        days_since = (now - last_dt).days
        if days_since < 1:
            continue
        trust = row["trust_score"]
        bond = row["bond_level"]
        # High-bond characters grow slowly, others decay
        if bond in ("trusted_ally", "soulbound"):
            delta = int(days_since * GROWTH_RATE)
            delta = min(delta, 5)  # Cap growth
        else:
            delta = int(days_since * DECAY_RATE)
            delta = max(delta, -10)  # Cap decay
        new_trust = max(0, min(100, trust + delta))
        if new_trust != trust:
            new_mood = _mood_from_trust(new_trust)
            new_bond = _bond_from_trust(new_trust)
            conn.execute(
                "UPDATE relationships SET trust_score=?, mood=?, bond_level=? WHERE character_name=?",
                (new_trust, new_mood, new_bond, row["character_name"]))
    conn.commit()
    conn.close()

def record_interaction(character_name: str, sentiment: str = "positive",
                       note: str = "") -> Dict:
    """sentiment: positive | negative | neutral | quest_complete | betrayal | gift"""
    rel = ensure_relationship(character_name)
    trust = rel["trust_score"]
    deltas = {
        "positive": 3, "negative": -4, "neutral": 0,
        "quest_complete": 5, "betrayal": -15, "gift": 8,
        "flirt": 4, "insult": -6, "help": 5, "attack": -10
    }
    delta = deltas.get(sentiment, 0)
    trust = max(0, min(100, trust + delta))
    mood = _mood_from_trust(trust)
    bond = _bond_from_trust(trust)
    count = rel["interaction_count"] + 1
    loyalty = max(0, min(100, rel["loyalty"] + (1 if delta >= 0 else -2)))
    reputation = max(0, min(100, rel["reputation"] + (1 if delta >= 0 else -1)))

    conn = get_conn()
    conn.execute(
        "UPDATE relationships SET trust_score=?, mood=?, interaction_count=?, "
        "bond_level=?, loyalty=?, reputation=?, last_interaction_at=? WHERE character_name=?",
        (trust, mood, count, bond, loyalty, reputation, now_iso(), character_name))
    conn.execute(
        "INSERT INTO relationship_events (character_name, sentiment, trust_delta, note, created_at) "
        "VALUES (?,?,?,?,?)",
        (character_name, sentiment, delta, note, now_iso()))
    conn.commit()
    conn.close()

    try:
        from core.safety import safety_monitor
        alerts = safety_monitor.evaluate_behavior(trust_delta=delta)
        if alerts:
            log.info("Relationship instability for %s: %s", character_name, alerts)
    except Exception:
        log.debug("suppressed error", exc_info=True)

    return get_relationship(character_name)

def get_event_history(character_name: str, limit: int = 50) -> List[Dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM relationship_events WHERE character_name=? ORDER BY id DESC LIMIT ?",
        (character_name, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def list_all_relationships() -> List[Dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM relationships ORDER BY trust_score DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_relationship_prompt(character_name: str) -> str:
    """Build relationship context for chat prompt injection."""
    rel = get_relationship(character_name)
    if not rel:
        return ""
    return (f"[Relationship with {character_name}: trust={rel['trust_score']}/100, "
            f"mood={rel['mood']}, bond={rel['bond_level']}, "
            f"loyalty={rel['loyalty']}/100, interactions={rel['interaction_count']}]")
