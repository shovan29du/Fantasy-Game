"""Tactical combat — D&D 5e SRD rules on a 16×16 grid.

Turn structure (5e action economy):
  • Movement  — up to MOVE_SPEED tiles; can split around Action
  • Action    — Attack, Cast Spell, Dash, Disengage, Dodge, Help
  • Bonus Action — off-hand light-weapon attack, some class features
  • Reaction  — Opportunity Attack when enemy leaves melee reach

Combat ends when all enemies are down (victory) or all player-side
units are incapacitated (defeat). Player characters who reach 0 HP
fall unconscious and make Death Saving Throws each turn (D&D 5e p.197).
Three successes = stabilised; three failures = dead.
"""
from __future__ import annotations

import json
import random
from collections import deque

from core.storage import get_conn, now_iso
from core.logging_setup import get_logger
from backend.app.domain import dnd_weapons as _dnd_weapons
from backend.app.domain import spells as _spells

log = get_logger(__name__)

# ── constants ────────────────────────────────────────────────────────────────
GRID_SIZE   = 16
MOVE_SPEED  = 6        # tiles per turn (30 ft / 5 ft per tile)
MOVE_POINTS = MOVE_SPEED   # alias used by older helpers

COMBAT_FEATS = {"Great Weapon Master", "Sharpshooter", "Alert", "Lucky", "Dual Wielder"}

# ── D&D SRD 5e monster stat blocks ───────────────────────────────────────────
# hp/ac/speed from SRD 5.2.1; damage simplified to one attack per action.
DND_MONSTERS: dict[str, dict] = {
    "Goblin":       {"hp": 7,  "ac": 15, "str_mod": -1, "dex_mod": 2, "con_mod": 0,
                     "proficiency": 2, "damage": "1d6+2", "speed": 6, "cr": 0.25,
                     "weapon": "Scimitar"},
    "Kobold":       {"hp": 5,  "ac": 12, "str_mod": -2, "dex_mod": 2, "con_mod": -1,
                     "proficiency": 2, "damage": "1d4+2", "speed": 6, "cr": 0.125},
    "Skeleton":     {"hp": 13, "ac": 13, "str_mod": 0,  "dex_mod": 2, "con_mod": -1,
                     "proficiency": 2, "damage": "1d6+2", "speed": 6, "cr": 0.25,
                     "weapon": "Shortsword"},
    "Zombie":       {"hp": 22, "ac": 8,  "str_mod": 3,  "dex_mod": -2, "con_mod": 3,
                     "proficiency": 2, "damage": "1d6+3", "speed": 4, "cr": 0.25},
    "Wolf":         {"hp": 11, "ac": 13, "str_mod": 2,  "dex_mod": 2, "con_mod": 1,
                     "proficiency": 2, "damage": "2d4+2", "speed": 8, "cr": 0.25},
    "Orc":          {"hp": 15, "ac": 13, "str_mod": 3,  "dex_mod": 1, "con_mod": 3,
                     "proficiency": 2, "damage": "1d12+3", "speed": 6, "cr": 0.5,
                     "weapon": "Greataxe"},
    "Hobgoblin":    {"hp": 11, "ac": 18, "str_mod": 1,  "dex_mod": 1, "con_mod": 1,
                     "proficiency": 2, "damage": "1d8+1", "speed": 6, "cr": 0.5,
                     "weapon": "Longsword"},
    "Bugbear":      {"hp": 27, "ac": 16, "str_mod": 3,  "dex_mod": 2, "con_mod": 1,
                     "proficiency": 2, "damage": "2d8+3", "speed": 6, "cr": 1,
                     "weapon": "Morningstar"},
    "Gnoll":        {"hp": 22, "ac": 15, "str_mod": 2,  "dex_mod": 1, "con_mod": 0,
                     "proficiency": 2, "damage": "2d6+2", "speed": 6, "cr": 0.5},
    "Cult Fanatic": {"hp": 33, "ac": 13, "str_mod": 0,  "dex_mod": 2, "con_mod": 1,
                     "proficiency": 2, "damage": "1d6+2", "speed": 6, "cr": 2,
                     "weapon": "Dagger"},
    "Bandit":       {"hp": 11, "ac": 12, "str_mod": 1,  "dex_mod": 1, "con_mod": 1,
                     "proficiency": 2, "damage": "1d6+1", "speed": 6, "cr": 0.125,
                     "weapon": "Scimitar"},
    "Ghoul":        {"hp": 22, "ac": 12, "str_mod": 1,  "dex_mod": 2, "con_mod": 0,
                     "proficiency": 2, "damage": "2d6+2", "speed": 6, "cr": 1},
    "Troll":        {"hp": 84, "ac": 15, "str_mod": 4,  "dex_mod": 1, "con_mod": 5,
                     "proficiency": 2, "damage": "2d6+4", "speed": 6, "cr": 5},
    "Wraith":       {"hp": 67, "ac": 13, "str_mod": -5, "dex_mod": 3, "con_mod": 0,
                     "proficiency": 3, "damage": "4d8+3", "speed": 0, "cr": 5},  # fly
}

# Monster pool by danger tier
_MONSTERS_BY_TIER: list[list[str]] = [
    ["Kobold", "Goblin"],                              # 0-1
    ["Goblin", "Skeleton", "Bandit"],                  # 2-3
    ["Orc", "Hobgoblin", "Zombie", "Wolf", "Gnoll"],   # 4-5
    ["Bugbear", "Ghoul", "Cult Fanatic"],               # 6-7
    ["Troll", "Wraith"],                                # 8-10
]

ALLY_DEFS = [
    ("Kael Ironroot", 2, -2, {"hp": 32, "max_hp": 32, "ac": 14,
                               "str_mod": 3, "dex_mod": 1, "con_mod": 2,
                               "proficiency": 2, "damage": "1d8+3"}),
    ("Seraphine",     2,  2, {"hp": 22, "max_hp": 22, "ac": 12,
                               "str_mod": 0, "dex_mod": 2, "con_mod": 1,
                               "proficiency": 2, "damage": "2d6+2",
                               "spell_mod": 3, "known_spells": ["Cure Wounds"]}),
]


# ── maths helpers ─────────────────────────────────────────────────────────────
def stat_mod(value: int | None) -> int:
    return ((value or 10) - 10) // 2


def proficiency_bonus(level: int | None) -> int:
    level = max(1, level or 1)
    if level >= 17: return 6
    if level >= 13: return 5
    if level >= 9:  return 4
    if level >= 5:  return 3
    return 2


def _roll_dice(spec, crit: bool = False) -> int:
    """Roll NdM+K, doubling dice (not mods) on a critical hit."""
    if not spec:
        return 0
    total = 0
    for term in str(spec).replace(" ", "").split("+"):
        if not term:
            continue
        if "d" in term.lower():
            n_str, m_str = term.lower().split("d")
            n = int(n_str) if n_str else 1
            if crit:
                n *= 2
            m = int(m_str)
            total += sum(random.randint(1, m) for _ in range(n))
        else:
            total += int(term)
    return total


def _d20(advantage: bool = False, disadvantage: bool = False) -> int:
    """Roll a d20 with optional advantage/disadvantage (5e rules)."""
    rolls = [random.randint(1, 20), random.randint(1, 20)]
    if advantage and not disadvantage:
        return max(rolls)
    if disadvantage and not advantage:
        return min(rolls)
    return rolls[0]


def _weapon_range_for(weapon_name: str | None, tier: int | None) -> int:
    weapon = _dnd_weapons.DND_WEAPONS.get(weapon_name) if weapon_name else None
    if weapon:
        if "Ranged" in weapon["category"]:
            return 4
        if "reach" in weapon.get("properties", []):
            return 2
        return 1
    # Ranged-ish at high tiers (sci-fi, generic high-tech)
    tier = 2 if tier is None else tier
    if tier <= 3: return 1
    if tier <= 6: return 3
    return 5


def _synthetic_weapon_damage(tier: int | None) -> str:
    tier = 2 if tier is None else tier
    if tier <= 1:  return "1d4"
    if tier <= 3:  return "1d6+1"
    if tier <= 6:  return "1d8+2"
    if tier <= 8:  return "1d10+3"
    return "2d6+3"


def _chebyshev(ax: int, ay: int, bx: int, by: int) -> int:
    return max(abs(ax - bx), abs(ay - by))


def _line_clear(obstacles: set, x1: int, y1: int, x2: int, y2: int) -> bool:
    steps = max(abs(x2 - x1), abs(y2 - y1))
    if steps <= 1:
        return True
    for i in range(1, steps):
        px = round(x1 + (x2 - x1) * i / steps)
        py = round(y1 + (y2 - y1) * i / steps)
        if (px, py) in obstacles:
            return False
    return True


def _random_obstacles(width: int, height: int, count: int, exclude: set) -> set:
    obstacles: set = set()
    attempts = 0
    while len(obstacles) < count and attempts < 500:
        attempts += 1
        pos = (random.randint(0, width - 1), random.randint(0, height - 1))
        if pos not in exclude and pos not in obstacles:
            obstacles.add(pos)
    return obstacles


def _bfs_reachable(start: tuple, obstacles: set, occupied: set,
                   width: int, height: int, points: int) -> dict:
    visited = {start: 0}
    q = deque([start])
    while q:
        cur = q.popleft()
        d = visited[cur]
        if d >= points:
            continue
        cx, cy = cur
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nxt = (cx + dx, cy + dy)
                if not (0 <= nxt[0] < width and 0 <= nxt[1] < height):
                    continue
                if nxt in obstacles or nxt in occupied or nxt in visited:
                    continue
                visited[nxt] = d + 1
                q.append(nxt)
    visited.pop(start, None)
    return visited


# ── turn-state helpers ────────────────────────────────────────────────────────
def _fresh_turn_state(unit_id: int, speed: int = MOVE_SPEED) -> dict:
    """Return a clean per-turn action-economy state for a unit."""
    return {
        "unit_id":            unit_id,
        "movement_remaining": speed,
        "action_used":        False,
        "bonus_used":         False,
        "has_reacted":        False,
        "disengage":          False,
        "dodge":              False,
    }


def _get_turn_state(encounter: dict) -> dict:
    try:
        return json.loads(encounter.get("turn_state_json", "{}") or "{}")
    except Exception:
        return {}


def _save_turn_state(conn, encounter_id: int, state: dict):
    conn.execute("UPDATE combat_encounters SET turn_state_json=? WHERE id=?",
                 (json.dumps(state), encounter_id))


# ── DB helpers ────────────────────────────────────────────────────────────────
def _ensure_turn_state_column():
    """Add turn_state_json column if it doesn't already exist (safe migration)."""
    conn = get_conn()
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(combat_encounters)").fetchall()]
        if "turn_state_json" not in cols:
            conn.execute("ALTER TABLE combat_encounters ADD COLUMN turn_state_json TEXT DEFAULT '{}'")
            conn.commit()
        if "encounter_id" not in [r[1] for r in conn.execute("PRAGMA table_info(combat_state)").fetchall()]:
            conn.execute("ALTER TABLE combat_state ADD COLUMN encounter_id INTEGER")
            conn.commit()
        if "stats_json" not in [r[1] for r in conn.execute("PRAGMA table_info(combat_state)").fetchall()]:
            conn.execute("ALTER TABLE combat_state ADD COLUMN stats_json TEXT DEFAULT '{}'")
            conn.commit()
    finally:
        conn.close()


_ensure_turn_state_column()


def _row_to_unit(row) -> dict:
    d = dict(row)
    try:
        d["stats"] = json.loads(d.pop("stats_json", "{}") or "{}")
    except Exception:
        d["stats"] = {}
    try:
        d["status_effects"] = json.loads(d.get("status_effects", "[]") or "[]")
    except Exception:
        d["status_effects"] = []
    return d


def get_encounter(encounter_id: int) -> dict | None:
    conn = get_conn()
    try:
        enc = conn.execute("SELECT * FROM combat_encounters WHERE id=?", (encounter_id,)).fetchone()
        if not enc:
            return None
        enc = dict(enc)
        enc["obstacles"]  = [tuple(o) for o in json.loads(enc.get("obstacles_json",  "[]") or "[]")]
        enc["turn_order"] = json.loads(enc.get("turn_order_json", "[]") or "[]")
        enc["log"]        = json.loads(enc.get("log_json",        "[]") or "[]")
        enc["turn_state"] = _get_turn_state(enc)
        units = [_row_to_unit(r) for r in
                 conn.execute("SELECT * FROM combat_state WHERE encounter_id=?", (encounter_id,)).fetchall()]
        by_id = {u["id"]: u for u in units}
        enc["units"] = [by_id[uid] for uid in enc["turn_order"] if uid in by_id]
        order = enc["turn_order"]
        idx   = enc["turn_index"]
        enc["current_unit_id"] = order[idx] if order and 0 <= idx < len(order) else None
        return enc
    finally:
        conn.close()


def get_active_encounter(session_id: str) -> dict | None:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id FROM combat_encounters WHERE session_id=? AND status='active' ORDER BY id DESC LIMIT 1",
            (session_id,)).fetchone()
    finally:
        conn.close()
    return get_encounter(row["id"]) if row else None


def _append_log(conn, encounter_id: int, lines: list[str]):
    if not lines:
        return
    row = conn.execute("SELECT log_json FROM combat_encounters WHERE id=?", (encounter_id,)).fetchone()
    try:
        existing = json.loads(row["log_json"] or "[]")
    except Exception:
        existing = []
    existing.extend(lines)
    conn.execute("UPDATE combat_encounters SET log_json=? WHERE id=?", (json.dumps(existing[-80:]), encounter_id))


# ── damage / death saves ──────────────────────────────────────────────────────
def _apply_damage(conn, target: dict, dmg: int, prefix: str) -> str:
    new_hp = max(0, target["hp"] - dmg)
    is_player = target["unit_type"] == "player"

    if new_hp <= 0 and is_player:
        # Player hits 0 — fall unconscious; enemy units just die
        conn.execute("UPDATE combat_state SET hp=0, status_effects=? WHERE id=?",
                     (json.dumps(_set_condition(target["status_effects"], "unconscious")), target["id"]))
        target["hp"] = 0
        target["status_effects"] = _set_condition(target["status_effects"], "unconscious")
        return f"{prefix} for {dmg} damage — {target['unit_name']} falls unconscious!"
    elif new_hp <= 0:
        conn.execute("UPDATE combat_state SET hp=0, is_active=0 WHERE id=?", (target["id"],))
        target["hp"] = 0
        target["is_active"] = 0
        return f"{prefix} for {dmg} damage — {target['unit_name']} is defeated!"
    else:
        # Extra damage to an already-unconscious player counts as a death-save failure
        was_unconscious = _has_condition(target["status_effects"], "unconscious")
        conn.execute("UPDATE combat_state SET hp=? WHERE id=?", (new_hp, target["id"]))
        target["hp"] = new_hp
        if was_unconscious:
            _add_death_failure(conn, target)
            return f"{prefix} for {dmg} damage on unconscious {target['unit_name']} (death failure!)."
        return f"{prefix} for {dmg} damage."


def _set_condition(effects: list[str], condition: str) -> list[str]:
    if condition not in effects:
        effects = list(effects) + [condition]
    return effects


def _remove_condition(effects: list[str], condition: str) -> list[str]:
    return [e for e in effects if e != condition]


def _has_condition(effects: list[str], condition: str) -> bool:
    return condition in effects


def _add_death_failure(conn, unit: dict):
    stats = unit.get("stats", {})
    stats["death_failures"] = stats.get("death_failures", 0) + 1
    conn.execute("UPDATE combat_state SET stats_json=? WHERE id=?", (json.dumps(stats), unit["id"]))
    if stats["death_failures"] >= 3:
        conn.execute("UPDATE combat_state SET is_active=0 WHERE id=?", (unit["id"],))


def _resolve_death_save(conn, unit: dict, encounter_id: int) -> str:
    """D&D 5e death saving throw — call on unconscious player's turn."""
    roll = random.randint(1, 20)
    stats = unit.get("stats", {})
    successes = stats.get("death_successes", 0)
    failures  = stats.get("death_failures",  0)

    if roll == 20:
        # Natural 20: regain 1 HP, regain consciousness
        stats["death_successes"] = 0
        stats["death_failures"]  = 0
        conn.execute("UPDATE combat_state SET hp=1, status_effects=?, stats_json=? WHERE id=?",
                     (json.dumps(_remove_condition(unit["status_effects"], "unconscious")),
                      json.dumps(stats), unit["id"]))
        return f"{unit['unit_name']} rolls a 20 on their death save — miraculous recovery! (1 HP)"

    if roll == 1:
        failures += 2
    elif roll >= 10:
        successes += 1
    else:
        failures += 1

    stats["death_successes"] = successes
    stats["death_failures"]  = failures
    conn.execute("UPDATE combat_state SET stats_json=? WHERE id=?", (json.dumps(stats), unit["id"]))

    if successes >= 3:
        stats["death_successes"] = 0
        stats["death_failures"]  = 0
        conn.execute("UPDATE combat_state SET status_effects=?, stats_json=? WHERE id=?",
                     (json.dumps(_remove_condition(unit["status_effects"], "unconscious")),
                      json.dumps(stats), unit["id"]))
        return f"{unit['unit_name']} stabilises (3 death-save successes)."
    if failures >= 3:
        conn.execute("UPDATE combat_state SET is_active=0 WHERE id=?", (unit["id"],))
        return f"{unit['unit_name']} has died (3 death-save failures)."

    result_word = "success" if roll >= 10 else "failure"
    extra = " (×2 failure for rolling 1!)" if roll == 1 else ""
    return (f"{unit['unit_name']} death save: {roll}{extra} — "
            f"{result_word}. ({successes}/3 saves, {failures}/3 fails)")


# ── attack / spell resolution ─────────────────────────────────────────────────
def _resolve_attack(conn, attacker: dict, defender: dict,
                    power_attack: bool = False,
                    advantage: bool = False,
                    disadvantage: bool = False) -> str:
    a_stats = attacker["stats"]
    finesse_or_ranged = a_stats.get("weapon_finesse_or_ranged", False)
    ability_mod = a_stats.get("dex_mod", 0) if finesse_or_ranged else a_stats.get("str_mod", 0)
    proficiency = a_stats.get("proficiency", 2)
    feats = a_stats.get("feats", [])

    power_attack = bool(power_attack) and (
        ("Great Weapon Master" in feats and not finesse_or_ranged) or
        ("Sharpshooter" in feats and finesse_or_ranged)
    )

    # Lucky feat — reroll a 1 once
    roll = _d20(advantage=advantage, disadvantage=disadvantage)
    if roll == 1 and "Lucky" in feats and not a_stats.get("luck_used"):
        roll = random.randint(1, 20)
        a_stats["luck_used"] = True
        conn.execute("UPDATE combat_state SET stats_json=? WHERE id=?", (json.dumps(a_stats), attacker["id"]))

    crit      = roll == 20
    auto_miss = roll == 1 and not advantage
    to_hit    = roll + ability_mod + proficiency - (5 if power_attack else 0)
    ac        = defender["stats"].get("ac", 10)
    hit       = not auto_miss and (crit or to_hit >= ac)

    weapon = a_stats.get("weapon_name")
    verb   = f"attacks {defender['unit_name']} with {weapon}" if weapon else f"attacks {defender['unit_name']}"
    if not hit:
        return f"{attacker['unit_name']} {verb} — misses (roll {to_hit} vs AC {ac})."
    dmg = (_roll_dice(a_stats.get("weapon_damage", "1d6"), crit=crit)
           + max(0, ability_mod) + (10 if power_attack else 0))
    prefix = f"{attacker['unit_name']} {verb} — hits{' (CRITICAL HIT!)' if crit else ''}"
    return _apply_damage(conn, defender, dmg, prefix)


def _resolve_spell(conn, caster: dict, spell_name: str, target: dict | None) -> str:
    spell     = _spells.SPELLS[spell_name]
    c_stats   = caster["stats"]
    spell_mod = c_stats.get("spell_mod", 0)
    prof      = c_stats.get("proficiency", 2)
    effect    = spell["effect_type"]

    if effect == "attack":
        if spell.get("auto_hit"):
            crit, hit = False, True
        else:
            roll = _d20()
            crit = roll == 20
            hit  = crit or (roll + spell_mod + prof) >= (target["stats"].get("ac", 10) if target else 10)
        if not hit:
            return f"{caster['unit_name']} casts {spell_name} at {target['unit_name']} — misses."
        dmg = _roll_dice(spell.get("damage", "1d6"), crit=crit)
        return _apply_damage(conn, target, dmg,
                             f"{caster['unit_name']} casts {spell_name} at {target['unit_name']}, hitting")

    if effect == "save":
        dc        = 8 + prof + spell_mod
        save_key  = spell.get("save_ability", "dexterity")[:3] + "_mod"
        save_mod  = target["stats"].get(save_key, 0) if target else 0
        saved     = (random.randint(1, 20) + save_mod) >= dc
        full_dmg  = _roll_dice(spell.get("damage", "0"))
        dmg       = full_dmg // 2 if saved else full_dmg
        verdict   = "partially resists" if saved else "fails to resist"
        if dmg <= 0:
            return f"{caster['unit_name']} casts {spell_name} — {target['unit_name']} {verdict} (DC {dc})."
        return _apply_damage(conn, target, dmg,
                             f"{caster['unit_name']} casts {spell_name} — {target['unit_name']} {verdict}")

    if effect == "heal":
        heal_target = target if target else caster
        amount  = _roll_dice(spell.get("heal", "1d8+3"))
        new_hp  = min(heal_target["max_hp"], heal_target["hp"] + amount)
        was_unc = _has_condition(heal_target["status_effects"], "unconscious")
        effects = _remove_condition(heal_target["status_effects"], "unconscious") if was_unc else heal_target["status_effects"]
        conn.execute("UPDATE combat_state SET hp=?, status_effects=? WHERE id=?",
                     (new_hp, json.dumps(effects), heal_target["id"]))
        woke = " They regain consciousness!" if was_unc else ""
        return f"{caster['unit_name']} casts {spell_name}, restoring {amount} HP to {heal_target['unit_name']}.{woke}"

    return f"{caster['unit_name']} casts {spell_name}. {spell.get('description', '')}"


# ── opportunity attacks ───────────────────────────────────────────────────────
def _opportunity_attacks(conn, encounter: dict, mover: dict,
                          old_x: int, old_y: int) -> list[str]:
    """Check whether any active enemies are adjacent to old_x,old_y but not
    to new_x,new_y and haven't reacted this round; if so, resolve one OA each."""
    logs: list[str] = []
    new_x, new_y = mover["x"], mover["y"]
    opposing = "enemy" if mover["unit_type"] == "player" else "player"
    for u in encounter["units"]:
        if u["unit_type"] != opposing or not u["is_active"]:
            continue
        # Only melee threats trigger OA (range 1)
        rng = _weapon_range_for(u["stats"].get("weapon_name"), u["stats"].get("weapon_tier"))
        if rng > 1:
            continue
        was_adjacent = _chebyshev(old_x, old_y, u["x"], u["y"]) <= 1
        still_adjacent = _chebyshev(new_x, new_y, u["x"], u["y"]) <= 1
        if not was_adjacent or still_adjacent:
            continue
        # Check reaction not already spent this round
        u_stats = u.get("stats", {})
        if u_stats.get("has_reacted_round"):
            continue
        # Mark reaction used
        u_stats["has_reacted_round"] = True
        conn.execute("UPDATE combat_state SET stats_json=? WHERE id=?", (json.dumps(u_stats), u["id"]))
        log_line = _resolve_attack(conn, u, mover)
        logs.append(f"OPPORTUNITY ATTACK — {log_line}")
    return logs


# ── AI turn resolution ────────────────────────────────────────────────────────
def _resolve_ai_unit_turn(conn, encounter: dict, unit: dict) -> list[str]:
    """AI turn: move toward nearest enemy, attack if in range.
    Uses full MOVE_SPEED movement budget (D&D 5e)."""
    units       = encounter["units"]
    opposing    = "enemy" if unit["unit_type"] == "player" else "player"
    targets     = [u for u in units if u["unit_type"] == opposing and u["is_active"]
                   and not _has_condition(u["status_effects"], "unconscious")]
    if not targets:
        return []

    target   = min(targets, key=lambda t: _chebyshev(unit["x"], unit["y"], t["x"], t["y"]))
    dist     = _chebyshev(unit["x"], unit["y"], target["x"], target["y"])
    rng      = _weapon_range_for(unit["stats"].get("weapon_name"), unit["stats"].get("weapon_tier"))
    obstacles = set(encounter["obstacles"])
    logs: list[str] = []

    # ── movement ──
    monster_speed = unit["stats"].get("speed", MOVE_SPEED)
    if dist > rng:
        occupied = {(u["x"], u["y"]) for u in units if u["is_active"] and u["id"] != unit["id"]}
        reachable = _bfs_reachable((unit["x"], unit["y"]), obstacles, occupied,
                                   encounter["grid_width"], encounter["grid_height"], monster_speed)
        if reachable:
            best    = min(reachable, key=lambda p: _chebyshev(p[0], p[1], target["x"], target["y"]))
            old_x, old_y = unit["x"], unit["y"]
            conn.execute("UPDATE combat_state SET x=?, y=? WHERE id=?", (best[0], best[1], unit["id"]))
            unit["x"], unit["y"] = best
            dist = _chebyshev(unit["x"], unit["y"], target["x"], target["y"])
            logs.append(f"{unit['unit_name']} moves toward {target['unit_name']}.")
            # OAs from the move (AI can provoke them too)
            oa_logs = _opportunity_attacks(conn, encounter, unit, old_x, old_y)
            logs.extend(oa_logs)

    # ── action: attack ──
    if dist <= rng:
        if rng > 1 and not _line_clear(obstacles, unit["x"], unit["y"], target["x"], target["y"]):
            logs.append(f"{unit['unit_name']}'s attack on {target['unit_name']} is blocked by an obstacle.")
        else:
            # Attacker has disadvantage if target is Dodging
            dodging = _has_condition(target["status_effects"], "dodge")
            logs.append(_resolve_attack(conn, unit, target,
                                        advantage=False, disadvantage=dodging))
    return logs


# ── turn advancement ──────────────────────────────────────────────────────────
def _check_outcome(units: list[dict]) -> str:
    enemies_alive  = any(u["unit_type"] == "enemy"  and u["is_active"] for u in units)
    players_active = any(u["unit_type"] == "player" and u["is_active"] and
                         not _has_condition(u["status_effects"], "unconscious") for u in units)
    players_exist  = any(u["unit_type"] == "player" and u["is_active"] for u in units)
    if not enemies_alive:
        return "won"
    if not players_exist:
        return "lost"
    return "active"


def _reset_round_reactions(conn, encounter_id: int):
    """Clear has_reacted_round on all units at the start of a new round."""
    rows = conn.execute("SELECT id, stats_json FROM combat_state WHERE encounter_id=?",
                        (encounter_id,)).fetchall()
    for row in rows:
        try:
            stats = json.loads(row["stats_json"] or "{}")
        except Exception:
            stats = {}
        if stats.get("has_reacted_round"):
            stats["has_reacted_round"] = False
            conn.execute("UPDATE combat_state SET stats_json=? WHERE id=?", (json.dumps(stats), row["id"]))


def _advance_turn(conn, encounter_id: int):
    """Advance to the next living unit; auto-resolve AI/ally turns until it
    is the human player's turn (or combat ends)."""
    while True:
        encounter = get_encounter(encounter_id)
        outcome   = _check_outcome(encounter["units"])
        if outcome != "active":
            conn.execute("UPDATE combat_encounters SET status=? WHERE id=?", (outcome, encounter_id))
            conn.commit()
            return

        order = encounter["turn_order"]
        by_id = {u["id"]: u for u in encounter["units"]}
        n     = len(order)
        idx   = encounter["turn_index"]
        prev_idx = idx
        found = False

        for _ in range(n):
            idx = (idx + 1) % n
            if by_id.get(order[idx], {}).get("is_active"):
                found = True
                break

        if not found:
            conn.execute("UPDATE combat_encounters SET status='lost' WHERE id=?", (encounter_id,))
            conn.commit()
            return

        # New round?
        new_round = encounter["round_number"] + (1 if idx <= prev_idx else 0)
        if new_round > encounter["round_number"]:
            _reset_round_reactions(conn, encounter_id)
            # Clear Dodge condition at round start
            for u in encounter["units"]:
                if _has_condition(u["status_effects"], "dodge"):
                    new_effects = _remove_condition(u["status_effects"], "dodge")
                    conn.execute("UPDATE combat_state SET status_effects=? WHERE id=?",
                                 (json.dumps(new_effects), u["id"]))

        conn.execute("UPDATE combat_encounters SET turn_index=?, round_number=? WHERE id=?",
                     (idx, new_round, encounter_id))
        conn.commit()

        current_unit = by_id[order[idx]]

        # Handle unconscious player: death saving throw on their turn
        if (_has_condition(current_unit.get("status_effects", []), "unconscious")
                and current_unit["unit_type"] == "player"):
            # Refresh unit from DB to get latest stats
            enc2  = get_encounter(encounter_id)
            unit2 = next((u for u in enc2["units"] if u["id"] == current_unit["id"]), None)
            if unit2:
                log_line = _resolve_death_save(conn, unit2, encounter_id)
                _append_log(conn, encounter_id, [log_line])
                conn.commit()
            # Still counts as their turn; skip to next
            continue

        if current_unit["stats"].get("is_human"):
            # Reset per-turn state for the human
            ts = _fresh_turn_state(current_unit["id"],
                                   speed=current_unit["stats"].get("speed", MOVE_SPEED))
            _save_turn_state(conn, encounter_id, ts)
            conn.commit()
            return

        # AI/ally turn — resolve immediately
        enc2 = get_encounter(encounter_id)
        unit = next(u for u in enc2["units"] if u["id"] == current_unit["id"])
        logs = _resolve_ai_unit_turn(conn, enc2, unit)
        _append_log(conn, encounter_id, logs)
        conn.commit()
        outcome = _check_outcome(get_encounter(encounter_id)["units"])
        if outcome != "active":
            conn.execute("UPDATE combat_encounters SET status=? WHERE id=?", (outcome, encounter_id))
            conn.commit()
            return


# ── build human unit ──────────────────────────────────────────────────────────
def _build_human_unit(conn, character_id: int | None, px: int, py: int) -> dict:
    from core.levelling import get_full_sheet

    sheet = get_full_sheet(character_id) if character_id else None
    if not sheet:
        base = {"str_mod": 1, "dex_mod": 1, "con_mod": 1, "int_mod": 0, "wis_mod": 0, "cha_mod": 0,
                "proficiency": 2, "ac": 11, "speed": MOVE_SPEED,
                "weapon_name": None, "weapon_tier": 2, "weapon_damage": "1d6",
                "weapon_finesse_or_ranged": False, "known_spells": [], "spell_mod": 0,
                "spell_ability": "intelligence", "feats": [], "character_id": character_id,
                "is_human": True, "spell_slots_max": {}, "spell_slots_used": {}}
        return {"unit_name": "Hero", "unit_type": "player", "hp": 30, "max_hp": 30, "x": px, "y": py,
                "initiative": random.randint(1, 20) + 1, "stats": base}

    total = sheet.get("total_stats", {})

    def mod(key):
        return stat_mod((total.get(key) or {}).get("total"))

    str_mod = mod("strength");   dex_mod = mod("dexterity");     con_mod = mod("constitution")
    int_mod = mod("intelligence"); wis_mod = mod("wisdom");       cha_mod = mod("charisma_stat")
    level       = sheet.get("calc_lv") or sheet.get("level") or 1
    proficiency = proficiency_bonus(level)

    # D&D 5e HP formula: hit-die-max + CON at lvl 1, then (die/2+1 + CON) per level
    profession = sheet.get("profession", "")
    hit_die = _hit_die_for(profession)
    max_hp  = (hit_die + con_mod) + max(0, level - 1) * (hit_die // 2 + 1 + con_mod)
    max_hp  = max(1, max_hp)

    feats        = [f for f in (sheet.get("traits") or []) if f in COMBAT_FEATS]
    armor_bonus  = 0
    weapon_name  = None
    weapon_tier  = 2

    for row in conn.execute(
        "SELECT item_name, item_type, stat_bonuses FROM inventory "
        "WHERE character_id=? AND equip_slot IS NOT NULL AND equip_slot != ''",
        (character_id,),
    ).fetchall():
        try:
            bonuses = json.loads(row["stat_bonuses"] or "{}")
        except Exception:
            bonuses = {}
        if row["item_type"] == "armor" and "ac_bonus" in bonuses:
            armor_bonus = max(armor_bonus, bonuses["ac_bonus"])
        elif row["item_name"] in _dnd_weapons.DND_WEAPONS:
            weapon_name = row["item_name"]
            weapon_tier = _dnd_weapons.weapon_tier_for(weapon_name)
        elif "weapon_tier" in bonuses:
            weapon_tier = max(weapon_tier, bonuses["weapon_tier"])

    if weapon_name:
        wdata               = _dnd_weapons.DND_WEAPONS[weapon_name]
        weapon_damage       = wdata["damage"]
        finesse_or_ranged   = _dnd_weapons.is_finesse_or_ranged(weapon_name)
    else:
        weapon_damage     = _synthetic_weapon_damage(weapon_tier)
        finesse_or_ranged = False

    # AC: no armour = 10+DEX; shield/armour adds bonus
    ac = 10 + dex_mod + armor_bonus

    # Spell slots by level (simplified SRD progression)
    known_spells   = [s for s in (sheet.get("spells") or []) if s in _spells.SPELLS]
    spell_ability  = _spells.casting_ability_for(profession)
    spell_mod_val  = {"intelligence": int_mod, "wisdom": wis_mod, "charisma_stat": cha_mod}.get(spell_ability, int_mod)
    slot_max       = _spell_slots_for(profession, level)

    initiative = random.randint(1, 20) + dex_mod + (5 if "Alert" in feats else 0)

    stats = {"str_mod": str_mod, "dex_mod": dex_mod, "con_mod": con_mod,
             "int_mod": int_mod, "wis_mod": wis_mod, "cha_mod": cha_mod,
             "proficiency": proficiency, "ac": ac, "speed": MOVE_SPEED,
             "weapon_name": weapon_name, "weapon_tier": weapon_tier,
             "weapon_damage": weapon_damage, "weapon_finesse_or_ranged": finesse_or_ranged,
             "known_spells": known_spells, "spell_mod": spell_mod_val, "spell_ability": spell_ability,
             "feats": feats, "character_id": character_id, "is_human": True,
             "spell_slots_max": slot_max, "spell_slots_used": {},
             "extra_attack": level >= 5 and _has_extra_attack(profession),
             "dual_wielder": "Dual Wielder" in feats}
    return {"unit_name": sheet.get("name", "Hero"), "unit_type": "player",
            "hp": max_hp, "max_hp": max_hp, "x": px, "y": py,
            "initiative": initiative, "stats": stats}


def _hit_die_for(profession: str) -> int:
    """D&D 5e hit die by class."""
    p = (profession or "").lower()
    if any(k in p for k in ["barbarian"]):           return 12
    if any(k in p for k in ["fighter", "paladin", "ranger"]): return 10
    if any(k in p for k in ["bard", "cleric", "druid", "monk", "rogue", "warlock",
                              "priest", "healer", "rogue", "assassin", "scout"]): return 8
    return 6  # Wizard, Sorcerer, others


def _spell_slots_for(profession: str, level: int) -> dict[str, int]:
    """Simplified full-caster slot progression (SRD Table)."""
    p = (profession or "").lower()
    is_caster = any(k in p for k in ["wizard", "sorcerer", "bard", "warlock", "cleric",
                                      "druid", "priest", "healer", "summoner", "necromancer",
                                      "illusionist", "enchanter"])
    is_half = any(k in p for k in ["paladin", "ranger", "eldritch"])
    if not is_caster and not is_half:
        return {}
    eff_level = level if is_caster else level // 2
    eff_level = max(1, eff_level)
    # Abbreviated slot table
    table = {
        1: {1: 2}, 2: {1: 3}, 3: {1: 4, 2: 2}, 4: {1: 4, 2: 3},
        5: {1: 4, 2: 3, 3: 2}, 6: {1: 4, 2: 3, 3: 3},
        7: {1: 4, 2: 3, 3: 3, 4: 1}, 8: {1: 4, 2: 3, 3: 3, 4: 2},
        9: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1}, 10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
    }
    entry = table.get(min(eff_level, 10), table[1])
    return {str(k): v for k, v in entry.items()}


def _has_extra_attack(profession: str) -> bool:
    p = (profession or "").lower()
    return any(k in p for k in ["fighter", "paladin", "ranger", "barbarian", "monk"])


# ── start encounter ───────────────────────────────────────────────────────────
def start_encounter(session_id: str, world_id: int | None, character_id: int | None,
                    danger: int = 4) -> dict:
    conn = get_conn()
    width = height = GRID_SIZE
    exclude: set[tuple[int, int]] = set()
    units: list[dict] = []

    px, py = 1, height // 2
    exclude.add((px, py))
    units.append(_build_human_unit(conn, character_id, px, py))

    danger = max(0, min(10, danger))

    # Allies
    for ally_name, ax, ay_offset, a_stats in ALLY_DEFS:
        pos = (ax, min(height - 1, max(0, py + ay_offset)))
        exclude.add(pos)
        stats = {**a_stats, "str_mod": a_stats.get("str_mod", 2), "dex_mod": 1, "con_mod": 1,
                 "proficiency": 2, "weapon_name": None, "weapon_tier": 2,
                 "weapon_damage": a_stats.get("damage", "1d6"),
                 "weapon_finesse_or_ranged": False, "feats": [], "character_id": None,
                 "speed": MOVE_SPEED,
                 "known_spells": a_stats.get("known_spells", []),
                 "spell_mod": a_stats.get("spell_mod", 0),
                 "spell_slots_max": {"1": 2} if a_stats.get("known_spells") else {},
                 "spell_slots_used": {}}
        units.append({"unit_name": ally_name, "unit_type": "player",
                      "hp": a_stats["hp"], "max_hp": a_stats["max_hp"],
                      "x": pos[0], "y": pos[1],
                      "initiative": random.randint(1, 20) + 1, "stats": stats})

    # Enemies from D&D monster pool
    tier  = min(4, danger // 2)
    pool  = _MONSTERS_BY_TIER[tier]
    enemy_count = 2 + min(4, danger // 2)
    ai_proficiency = proficiency_bonus(2 + danger // 3)

    for i in range(enemy_count):
        mname = random.choice(pool)
        mdata = DND_MONSTERS[mname]
        while True:
            pos = (random.randint(width - 7, width - 1), random.randint(0, height - 1))
            if pos not in exclude:
                break
        exclude.add(pos)
        e_dmg = mdata.get("damage", "1d6+1")
        e_ac  = mdata["ac"]
        e_hp  = mdata["hp"]
        e_stats = {
            "str_mod":   mdata.get("str_mod", 0),
            "dex_mod":   mdata.get("dex_mod", 0),
            "con_mod":   mdata.get("con_mod", 0),
            "proficiency": ai_proficiency,
            "ac":        e_ac,
            "speed":     mdata.get("speed", MOVE_SPEED),
            "weapon_name":  mdata.get("weapon"),
            "weapon_tier":  2,
            "weapon_damage":e_dmg,
            "weapon_finesse_or_ranged": False,
            "feats": [], "character_id": None,
        }
        initiative = random.randint(1, 20) + mdata.get("dex_mod", 0)
        units.append({"unit_name": f"{mname} {i + 1}", "unit_type": "enemy",
                      "hp": e_hp, "max_hp": e_hp, "x": pos[0], "y": pos[1],
                      "initiative": initiative, "stats": e_stats})

    obstacles = _random_obstacles(width, height, random.randint(20, 30), exclude)

    cur = conn.execute(
        "INSERT INTO combat_encounters "
        "(session_id,world_id,character_id,grid_width,grid_height,obstacles_json,"
        "turn_order_json,turn_index,round_number,status,log_json,turn_state_json,created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (session_id, world_id, character_id, width, height,
         json.dumps([list(o) for o in obstacles]),
         "[]", 0, 1, "active",
         json.dumps([f"⚔ Combat begins! {enemy_count} {', '.join(pool)} emerge from the shadows."]),
         "{}", now_iso()),
    )
    encounter_id = cur.lastrowid

    unit_ids = []
    for u in units:
        cur2 = conn.execute(
            "INSERT INTO combat_state "
            "(session_id,unit_name,unit_type,hp,max_hp,x,y,status_effects,"
            "initiative,is_active,encounter_id,stats_json) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (session_id, u["unit_name"], u["unit_type"], u["hp"], u["max_hp"],
             u["x"], u["y"], "[]", u["initiative"], 1, encounter_id,
             json.dumps(u["stats"])),
        )
        unit_ids.append(cur2.lastrowid)

    # Sort by initiative (descending)
    order = [uid for uid, _ in sorted(zip(unit_ids, [u["initiative"] for u in units]),
                                       key=lambda p: -p[1])]
    conn.execute("UPDATE combat_encounters SET turn_order_json=? WHERE id=?",
                 (json.dumps(order), encounter_id))
    conn.commit()

    # Advance to first human turn (skipping leading AI turns)
    by_id_local = {uid: u for uid, u in zip(unit_ids, units)}
    first_unit  = by_id_local[order[0]]
    if not first_unit["stats"].get("is_human"):
        conn.execute("UPDATE combat_encounters SET turn_index=-1 WHERE id=?", (encounter_id,))
        conn.commit()
        _advance_turn(conn, encounter_id)
        conn.commit()
    else:
        # First mover is human — set up turn state
        ts = _fresh_turn_state(order[0], first_unit["stats"].get("speed", MOVE_SPEED))
        _save_turn_state(conn, encounter_id, ts)
        conn.commit()

    conn.close()
    return get_encounter(encounter_id)


# ── player-action endpoints ───────────────────────────────────────────────────
def _require_human_turn(encounter: dict, unit_id: int) -> dict | None:
    if encounter["status"] != "active":
        return {"error": "Combat has already ended."}
    if encounter["current_unit_id"] != unit_id:
        return {"error": "It is not that unit's turn."}
    return None


def move_unit(encounter_id: int, unit_id: int, x: int, y: int) -> dict:
    """Move the player unit to (x,y) — uses movement budget, does NOT end turn."""
    encounter = get_encounter(encounter_id)
    if not encounter:
        return {"error": "Encounter not found."}
    err = _require_human_turn(encounter, unit_id)
    if err:
        return err

    unit = next((u for u in encounter["units"] if u["id"] == unit_id), None)
    if not unit:
        return {"error": "Unit not found."}

    ts = _get_turn_state(encounter)
    remaining = ts.get("movement_remaining", MOVE_SPEED)
    if remaining <= 0:
        return {"error": "No movement remaining this turn. End your turn or Dash first."}

    obstacles = set(encounter["obstacles"])
    occupied  = {(u["x"], u["y"]) for u in encounter["units"] if u["is_active"] and u["id"] != unit_id}
    reachable = _bfs_reachable((unit["x"], unit["y"]), obstacles, occupied,
                               encounter["grid_width"], encounter["grid_height"], remaining)
    if (x, y) not in reachable:
        return {"error": "That tile is out of movement range, blocked, or occupied."}

    conn = get_conn()
    try:
        steps_used = reachable[(x, y)]
        old_x, old_y = unit["x"], unit["y"]
        conn.execute("UPDATE combat_state SET x=?, y=? WHERE id=?", (x, y, unit_id))
        unit["x"], unit["y"] = x, y

        # Opportunity attacks from enemies in old position
        if not ts.get("disengage"):
            oa_logs = _opportunity_attacks(conn, encounter, unit, old_x, old_y)
            _append_log(conn, encounter_id, oa_logs)

        _append_log(conn, encounter_id, [f"📍 {unit['unit_name']} moves ({steps_used} tile{'s' if steps_used != 1 else ''})."])

        ts["movement_remaining"] = remaining - steps_used
        _save_turn_state(conn, encounter_id, ts)
        conn.commit()
    finally:
        conn.close()
    return get_encounter(encounter_id)


def attack_unit(encounter_id: int, unit_id: int, target_id: int,
                power_attack: bool = False) -> dict:
    """Make a weapon attack — uses the Action for the turn, does NOT end turn."""
    encounter = get_encounter(encounter_id)
    if not encounter:
        return {"error": "Encounter not found."}
    err = _require_human_turn(encounter, unit_id)
    if err:
        return err

    ts = _get_turn_state(encounter)
    if ts.get("action_used"):
        return {"error": "You have already used your Action this turn."}

    unit   = next((u for u in encounter["units"] if u["id"] == unit_id), None)
    target = next((u for u in encounter["units"] if u["id"] == target_id), None)
    if not unit or not target or not target["is_active"]:
        return {"error": "Invalid target."}
    if _has_condition(target["status_effects"], "unconscious"):
        return {"error": "That unit is already unconscious."}
    if target["unit_type"] == unit["unit_type"]:
        return {"error": "That unit is not an enemy."}

    dist = _chebyshev(unit["x"], unit["y"], target["x"], target["y"])
    rng  = _weapon_range_for(unit["stats"].get("weapon_name"), unit["stats"].get("weapon_tier"))
    if dist > rng:
        return {"error": f"Target is out of range (weapon range {rng}, distance {dist})."}
    obstacles = set(encounter["obstacles"])
    if rng > 1 and not _line_clear(obstacles, unit["x"], unit["y"], target["x"], target["y"]):
        return {"error": "An obstacle blocks line of fire."}

    conn = get_conn()
    try:
        # Dodge: attacks vs a dodging target have disadvantage
        dodging = _has_condition(target["status_effects"], "dodge")
        message = _resolve_attack(conn, unit, target, power_attack=power_attack,
                                  disadvantage=dodging)
        _append_log(conn, encounter_id, [message])
        conn.commit()

        # Extra Attack (fighters etc. at lv 5+)
        if unit["stats"].get("extra_attack") and not ts.get("extra_attack_used"):
            ts["extra_attack_used"] = True
            _save_turn_state(conn, encounter_id, ts)
            conn.commit()
            # Return without marking action_used — extra attack fires via another attack call
            return get_encounter(encounter_id)

        ts["action_used"] = True
        _save_turn_state(conn, encounter_id, ts)
        outcome = _check_outcome(get_encounter(encounter_id)["units"])
        if outcome != "active":
            conn.execute("UPDATE combat_encounters SET status=? WHERE id=?", (outcome, encounter_id))
        conn.commit()
    finally:
        conn.close()
    return get_encounter(encounter_id)


def cast_spell(encounter_id: int, unit_id: int, spell_name: str,
               target_id: int | None) -> dict:
    """Cast a spell — uses the Action, may consume a spell slot."""
    encounter = get_encounter(encounter_id)
    if not encounter:
        return {"error": "Encounter not found."}
    err = _require_human_turn(encounter, unit_id)
    if err:
        return err

    ts = _get_turn_state(encounter)
    if ts.get("action_used"):
        return {"error": "You have already used your Action this turn."}

    unit = next((u for u in encounter["units"] if u["id"] == unit_id), None)
    if not unit:
        return {"error": "Unit not found."}
    if spell_name not in _spells.SPELLS:
        return {"error": f"Unknown spell: {spell_name}"}
    if spell_name not in unit["stats"].get("known_spells", []):
        return {"error": "You don't know that spell."}

    spell = _spells.SPELLS[spell_name]
    level = spell.get("level", 0)

    # Check & consume spell slot (cantrips = level 0, always available)
    if level > 0:
        slots_max  = unit["stats"].get("spell_slots_max", {})
        slots_used = unit["stats"].get("spell_slots_used", {})
        slot_key   = str(level)
        max_slots  = slots_max.get(slot_key, 0)
        used_slots = slots_used.get(slot_key, 0)
        if used_slots >= max_slots:
            return {"error": f"No level-{level} spell slots remaining."}
        slots_used[slot_key] = used_slots + 1
        unit["stats"]["spell_slots_used"] = slots_used
        conn2 = get_conn()
        conn2.execute("UPDATE combat_state SET stats_json=? WHERE id=?",
                      (json.dumps(unit["stats"]), unit["id"]))
        conn2.commit()
        conn2.close()

    target = None
    if target_id is not None:
        target = next((u for u in encounter["units"] if u["id"] == target_id), None)

    conn = get_conn()
    try:
        message = _resolve_spell(conn, unit, spell_name, target)
        _append_log(conn, encounter_id, [message])
        ts["action_used"] = True
        _save_turn_state(conn, encounter_id, ts)
        outcome = _check_outcome(get_encounter(encounter_id)["units"])
        if outcome != "active":
            conn.execute("UPDATE combat_encounters SET status=? WHERE id=?", (outcome, encounter_id))
        conn.commit()
    finally:
        conn.close()
    return get_encounter(encounter_id)


def special_action(encounter_id: int, unit_id: int, action: str) -> dict:
    """Handle Dash / Disengage / Dodge / Help — each costs the Action.

    dash       — add MOVE_SPEED extra movement for this turn
    disengage  — movement provokes no opportunity attacks this turn
    dodge      — attackers have disadvantage until start of next turn
    help       — give an ally advantage on their next attack (narrative only for now)
    """
    encounter = get_encounter(encounter_id)
    if not encounter:
        return {"error": "Encounter not found."}
    err = _require_human_turn(encounter, unit_id)
    if err:
        return err

    ts = _get_turn_state(encounter)
    if ts.get("action_used"):
        return {"error": "You have already used your Action this turn."}

    unit = next((u for u in encounter["units"] if u["id"] == unit_id), None)
    if not unit:
        return {"error": "Unit not found."}

    action = action.lower()
    conn = get_conn()
    try:
        if action == "dash":
            extra = unit["stats"].get("speed", MOVE_SPEED)
            ts["movement_remaining"] = ts.get("movement_remaining", MOVE_SPEED) + extra
            ts["action_used"] = True
            _append_log(conn, encounter_id,
                        [f"🏃 {unit['unit_name']} Dashes — +{extra} tiles of movement."])

        elif action == "disengage":
            ts["disengage"]   = True
            ts["action_used"] = True
            _append_log(conn, encounter_id,
                        [f"🔒 {unit['unit_name']} Disengages — movement won't provoke opportunity attacks."])

        elif action == "dodge":
            ts["action_used"] = True
            # Apply Dodge condition to the unit
            effects = _set_condition(unit["status_effects"], "dodge")
            conn.execute("UPDATE combat_state SET status_effects=? WHERE id=?",
                         (json.dumps(effects), unit["id"]))
            _append_log(conn, encounter_id,
                        [f"🛡 {unit['unit_name']} Dodges — attackers have disadvantage until next turn."])

        elif action == "help":
            ts["action_used"] = True
            _append_log(conn, encounter_id,
                        [f"🤝 {unit['unit_name']} takes the Help action."])

        else:
            conn.close()
            return {"error": f"Unknown action '{action}'."}

        _save_turn_state(conn, encounter_id, ts)
        conn.commit()
    finally:
        conn.close()
    return get_encounter(encounter_id)


def end_turn(encounter_id: int, unit_id: int) -> dict:
    """Explicitly end the player's turn and advance to the next unit."""
    encounter = get_encounter(encounter_id)
    if not encounter:
        return {"error": "Encounter not found."}
    if encounter["status"] != "active":
        return encounter
    if encounter["current_unit_id"] != unit_id:
        return {"error": "It is not that unit's turn."}

    conn = get_conn()
    try:
        _append_log(conn, encounter_id, [])
        _advance_turn(conn, encounter_id)
        conn.commit()
    finally:
        conn.close()
    return get_encounter(encounter_id)
