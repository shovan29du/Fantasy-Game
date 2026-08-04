"""AiChat Pro — Companion Soul Engine (from Backyard.ai)
10 affect dimensions + 9 regulation styles.
Emotional state evolves based on chat interactions."""

from core.logging_setup import get_logger

log = get_logger(__name__)
import json
from core.storage import get_conn, now_iso

DEFAULT_AFFECT = {
    "warmth": 0.45, "trust": 0.35, "calm": 0.65, "vulnerability": 0.2,
    "longing": 0.15, "hurt": 0.05, "tension": 0.1, "irritation": 0.05,
    "affection_intensity": 0.25, "reassurance_need": 0.15,
}
DEFAULT_REGULATION = {
    "suppression": 0.35, "volatility": 0.25, "recovery_speed": 0.55,
    "conflict_avoidance": 0.45, "reassurance_seeking": 0.4,
    "protest_behavior": 0.2, "emotional_transparency": 0.55,
    "attachment_activation": 0.45, "pride": 0.3,
}

def get_soul(character_name: str) -> dict:
    conn = get_conn()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (f"soul_{character_name}",)).fetchone()
    conn.close()
    if row:
        try: return json.loads(row["value"])
        except Exception:
            log.debug("suppressed error", exc_info=True)
            pass
    return {"affect": dict(DEFAULT_AFFECT), "regulation": dict(DEFAULT_REGULATION),
            "essence": "", "voice_style": "", "relational_style": ""}

def save_soul(character_name: str, soul: dict):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)",
                 (f"soul_{character_name}", json.dumps(soul)))
    conn.commit(); conn.close()

def update_affect(character_name: str, sentiment: str):
    """Update emotional state based on interaction sentiment."""
    soul = get_soul(character_name)
    affect = soul.get("affect", dict(DEFAULT_AFFECT))
    reg = soul.get("regulation", dict(DEFAULT_REGULATION))
    volatility = reg.get("volatility", 0.25)
    recovery = reg.get("recovery_speed", 0.55)
    delta_map = {
        "positive": {"warmth": 0.05, "trust": 0.03, "calm": 0.02, "hurt": -0.02, "tension": -0.03},
        "negative": {"warmth": -0.05, "trust": -0.04, "hurt": 0.08, "tension": 0.06, "irritation": 0.05, "calm": -0.05},
        "flirt": {"warmth": 0.08, "affection_intensity": 0.1, "longing": 0.05, "vulnerability": 0.03},
        "neutral": {"calm": 0.01 * recovery, "tension": -0.01 * recovery, "hurt": -0.01 * recovery},
        "betrayal": {"trust": -0.15, "hurt": 0.2, "tension": 0.15, "warmth": -0.1, "irritation": 0.1},
        "gift": {"warmth": 0.1, "trust": 0.05, "affection_intensity": 0.08},
        "attack": {"hurt": 0.15, "tension": 0.2, "trust": -0.1, "calm": -0.1, "irritation": 0.15},
        "comfort": {"calm": 0.08, "trust": 0.05, "hurt": -0.05, "vulnerability": 0.05, "reassurance_need": -0.05},
    }
    deltas = delta_map.get(sentiment, delta_map["neutral"])
    for k, d in deltas.items():
        scaled = d * (1 + volatility)
        affect[k] = max(0, min(1, affect.get(k, 0.5) + scaled))
    soul["affect"] = affect
    save_soul(character_name, soul)
    return affect

def build_soul_prompt(character_name: str) -> str:
    """Build emotional state context for chat prompt injection."""
    soul = get_soul(character_name)
    affect = soul.get("affect", DEFAULT_AFFECT)
    # Only mention notable states (>0.5 or <0.1)
    notable = []
    for k, v in affect.items():
        label = k.replace("_", " ")
        if v >= 0.7: notable.append(f"strongly feeling {label}")
        elif v >= 0.5: notable.append(f"moderate {label}")
        elif v <= 0.1 and k in ("trust", "calm", "warmth"): notable.append(f"very low {label}")
    if not notable: return ""
    essence = soul.get("essence", "")
    voice = soul.get("voice_style", "")
    parts = [f"[Emotional state: {', '.join(notable[:5])}]"]
    if essence: parts.append(f"[Soul essence: {essence}]")
    if voice: parts.append(f"[Voice style: {voice}]")
    return " ".join(parts)
