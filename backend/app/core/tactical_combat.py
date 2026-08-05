"""Turn-based tactical combat on an 8x8 grid board -- obstacles, initiative
order, D&D-style attack/damage/saving-throw math, weapon attacks, spells,
and feats, with one move-or-attack-or-cast action per turn. Enemy and ally
units resolve their own turns automatically (simple "close the distance,
then swing" AI); the frontend only ever needs to act for the one
human-controlled unit.
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

GRID_SIZE = 8
MOVE_POINTS = 3
ENEMY_NAMES = ["Raider", "Cultist", "Marauder", "Feral Beast", "Drone", "Ghoul", "Bandit", "Wraith"]
ALLY_DEFS = [("Kael Ironroot", 2, -2), ("Seraphine", 2, 2)]  # (name, x, y-offset from player row)

# Feats whose combat effect this engine actually simulates (see
# core.levelling.DND_FEATS for the full list, most of which are already
# expressed purely as stat bonuses applied at learn-time).
COMBAT_FEATS = {"Great Weapon Master", "Sharpshooter", "Alert", "Lucky", "Dual Wielder"}


def stat_mod(value: int | None) -> int:
    return ((value or 10) - 10) // 2


def proficiency_bonus(level: int | None) -> int:
    level = max(1, level or 1)
    if level >= 17:
        return 6
    if level >= 13:
        return 5
    if level >= 9:
        return 4
    if level >= 5:
        return 3
    return 2


def _roll_dice(spec, crit: bool = False) -> int:
    """Sum one or more `NdM` terms (optionally `+K` flat terms), e.g.
    '3d4+3' or '4d6+2d8'. On a critical hit the number of dice (not flat
    modifiers) is doubled, per standard D&D crit rules."""
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


def _synthetic_weapon_damage(tier: int | None) -> str:
    """Damage dice for units without a real D&D weapon match (sci-fi loot,
    generic ally/enemy stat blocks), scaled by the multiverse weapon tier."""
    tier = 2 if tier is None else tier
    if tier <= 1:
        return "1d4"
    if tier <= 3:
        return "1d6"
    if tier <= 6:
        return "1d8"
    if tier <= 8:
        return "1d10"
    return "2d6"


def _weapon_range_for(weapon_name: str | None, tier: int | None) -> int:
    weapon = _dnd_weapons.DND_WEAPONS.get(weapon_name) if weapon_name else None
    if weapon:
        if "Ranged" in weapon["category"]:
            return 4
        if "reach" in weapon.get("properties", []):
            return 2
        return 1
    tier = 2 if tier is None else tier
    if tier <= 3:
        return 1
    if tier <= 6:
        return 3
    return 5


def _chebyshev(ax: int, ay: int, bx: int, by: int) -> int:
    return max(abs(ax - bx), abs(ay - by))


def _line_clear(obstacles: set[tuple[int, int]], x1: int, y1: int, x2: int, y2: int) -> bool:
    steps = max(abs(x2 - x1), abs(y2 - y1))
    if steps <= 1:
        return True
    for i in range(1, steps):
        px = round(x1 + (x2 - x1) * i / steps)
        py = round(y1 + (y2 - y1) * i / steps)
        if (px, py) in obstacles:
            return False
    return True


def _random_obstacles(width: int, height: int, count: int, exclude: set[tuple[int, int]]) -> set[tuple[int, int]]:
    obstacles: set[tuple[int, int]] = set()
    attempts = 0
    while len(obstacles) < count and attempts < 300:
        attempts += 1
        pos = (random.randint(0, width - 1), random.randint(0, height - 1))
        if pos in exclude or pos in obstacles:
            continue
        obstacles.add(pos)
    return obstacles


def _bfs_reachable(start: tuple[int, int], obstacles: set, occupied: set, width: int, height: int, points: int) -> dict:
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
        enc["obstacles"] = [tuple(o) for o in json.loads(enc.get("obstacles_json", "[]") or "[]")]
        enc["turn_order"] = json.loads(enc.get("turn_order_json", "[]") or "[]")
        enc["log"] = json.loads(enc.get("log_json", "[]") or "[]")
        units = [_row_to_unit(r) for r in
                 conn.execute("SELECT * FROM combat_state WHERE encounter_id=?", (encounter_id,)).fetchall()]
        by_id = {u["id"]: u for u in units}
        enc["units"] = [by_id[uid] for uid in enc["turn_order"] if uid in by_id]
        order = enc["turn_order"]
        idx = enc["turn_index"]
        enc["current_unit_id"] = order[idx] if order and 0 <= idx < len(order) else None
        return enc
    finally:
        conn.close()


def _append_log(conn, encounter_id: int, lines: list[str]):
    if not lines:
        return
    row = conn.execute("SELECT log_json FROM combat_encounters WHERE id=?", (encounter_id,)).fetchone()
    try:
        existing = json.loads(row["log_json"] or "[]")
    except Exception:
        existing = []
    existing.extend(lines)
    conn.execute("UPDATE combat_encounters SET log_json=? WHERE id=?", (json.dumps(existing[-60:]), encounter_id))


def _apply_damage(conn, target: dict, dmg: int, prefix: str) -> str:
    new_hp = max(0, target["hp"] - dmg)
    conn.execute("UPDATE combat_state SET hp=?, is_active=? WHERE id=?", (new_hp, 1 if new_hp > 0 else 0, target["id"]))
    target["hp"] = new_hp
    if new_hp <= 0:
        target["is_active"] = 0
        return f"{prefix} for {dmg} damage -- {target['unit_name']} is defeated!"
    return f"{prefix} for {dmg} damage."


def _resolve_attack(conn, attacker: dict, defender: dict, power_attack: bool = False) -> str:
    """A D&D-style weapon attack: d20 + ability modifier + proficiency vs
    the target's AC. Finesse/ranged weapons use Dex; everything else uses
    Str. Great Weapon Master / Sharpshooter may trade -5 to hit for +10
    damage; Lucky lets the attacker reroll a natural 1, once per combat."""
    a_stats = attacker["stats"]
    finesse_or_ranged = a_stats.get("weapon_finesse_or_ranged", False)
    ability_mod = a_stats.get("dex_mod", 0) if finesse_or_ranged else a_stats.get("str_mod", 0)
    proficiency = a_stats.get("proficiency", 2)
    feats = a_stats.get("feats", [])
    power_attack = bool(power_attack) and (
        ("Great Weapon Master" in feats and not finesse_or_ranged) or
        ("Sharpshooter" in feats and finesse_or_ranged)
    )

    roll = random.randint(1, 20)
    if roll == 1 and "Lucky" in feats and not a_stats.get("luck_used"):
        roll = random.randint(1, 20)
        a_stats["luck_used"] = True
        conn.execute("UPDATE combat_state SET stats_json=? WHERE id=?", (json.dumps(a_stats), attacker["id"]))

    crit = roll == 20
    auto_miss = roll == 1
    attack_total = roll + ability_mod + proficiency - (5 if power_attack else 0)
    defense_total = defender["stats"].get("ac", 10)
    hit = not auto_miss and (crit or attack_total >= defense_total)

    weapon_name = a_stats.get("weapon_name")
    verb = f"attacks {defender['unit_name']} with {weapon_name}" if weapon_name else f"attacks {defender['unit_name']}"
    if not hit:
        return f"{attacker['unit_name']} {verb} but misses (roll {attack_total} vs AC {defense_total})."
    dmg = _roll_dice(a_stats.get("weapon_damage", "1d6"), crit=crit) + max(0, ability_mod) + (10 if power_attack else 0)
    prefix = f"{attacker['unit_name']} {verb} and hits{' (critical!)' if crit else ''}"
    return _apply_damage(conn, defender, dmg, prefix)


def _resolve_spell(conn, caster: dict, spell_name: str, target: dict | None) -> str:
    spell = _spells.SPELLS[spell_name]
    c_stats = caster["stats"]
    spell_mod = c_stats.get("spell_mod", 0)
    proficiency = c_stats.get("proficiency", 2)
    effect = spell["effect_type"]

    if effect == "attack":
        if spell.get("auto_hit"):
            crit, hit = False, True
        else:
            roll = random.randint(1, 20)
            crit = roll == 20
            attack_total = roll + spell_mod + proficiency
            hit = crit or attack_total >= target["stats"].get("ac", 10)
        if not hit:
            return f"{caster['unit_name']} casts {spell_name} at {target['unit_name']} but it misses."
        dmg = _roll_dice(spell.get("damage", "1d6"), crit=crit)
        return _apply_damage(conn, target, dmg, f"{caster['unit_name']} casts {spell_name} at {target['unit_name']}, hitting")

    if effect == "save":
        dc = 8 + proficiency + spell_mod
        save_ability = spell.get("save_ability", "dexterity")
        save_mod = target["stats"].get(f"{save_ability[:3]}_mod", 0)
        saved = (random.randint(1, 20) + save_mod) >= dc
        full_dmg = _roll_dice(spell.get("damage", "0"))
        dmg = full_dmg // 2 if saved else full_dmg
        verdict = "partially resists" if saved else "fails to resist"
        if dmg <= 0:
            return f"{caster['unit_name']} casts {spell_name} -- {target['unit_name']} {verdict} (DC {dc})."
        return _apply_damage(conn, target, dmg, f"{caster['unit_name']} casts {spell_name} -- {target['unit_name']} {verdict}")

    if effect == "heal":
        heal_target = target or caster
        amount = _roll_dice(spell.get("heal", "1d8"))
        new_hp = min(heal_target["max_hp"], heal_target["hp"] + amount)
        conn.execute("UPDATE combat_state SET hp=? WHERE id=?", (new_hp, heal_target["id"]))
        heal_target["hp"] = new_hp
        return f"{caster['unit_name']} casts {spell_name}, healing {heal_target['unit_name']} for {amount} HP."

    return f"{caster['unit_name']} casts {spell_name}. {spell.get('description', '')}"


def _resolve_ai_unit_turn(conn, encounter: dict, unit: dict) -> list[str]:
    units = encounter["units"]
    opposing_type = "enemy" if unit["unit_type"] == "player" else "player"
    targets = [u for u in units if u["unit_type"] == opposing_type and u["is_active"]]
    if not targets:
        return []
    target = min(targets, key=lambda t: _chebyshev(unit["x"], unit["y"], t["x"], t["y"]))
    dist = _chebyshev(unit["x"], unit["y"], target["x"], target["y"])
    rng = _weapon_range_for(unit["stats"].get("weapon_name"), unit["stats"].get("weapon_tier"))
    obstacles = set(encounter["obstacles"])
    logs = []
    if dist > rng:
        occupied = {(u["x"], u["y"]) for u in units if u["is_active"] and u["id"] != unit["id"]}
        reachable = _bfs_reachable((unit["x"], unit["y"]), obstacles, occupied, encounter["grid_width"], encounter["grid_height"], MOVE_POINTS)
        if reachable:
            best = min(reachable, key=lambda p: _chebyshev(p[0], p[1], target["x"], target["y"]))
            conn.execute("UPDATE combat_state SET x=?, y=? WHERE id=?", (best[0], best[1], unit["id"]))
            unit["x"], unit["y"] = best
            logs.append(f"{unit['unit_name']} moves toward {target['unit_name']}.")
            dist = _chebyshev(unit["x"], unit["y"], target["x"], target["y"])
    if dist <= rng:
        if rng > 1 and not _line_clear(obstacles, unit["x"], unit["y"], target["x"], target["y"]):
            logs.append(f"{unit['unit_name']}'s attack on {target['unit_name']} is blocked by an obstacle.")
        else:
            logs.append(_resolve_attack(conn, unit, target))
    return logs


def _check_outcome(units: list[dict]) -> str:
    enemies_alive = any(u["unit_type"] == "enemy" and u["is_active"] for u in units)
    players_alive = any(u["unit_type"] == "player" and u["is_active"] for u in units)
    if not enemies_alive:
        return "won"
    if not players_alive:
        return "lost"
    return "active"


def _advance_turn(conn, encounter_id: int):
    """Move the turn pointer to the next living unit in initiative order
    (wrapping around and incrementing the round as needed), then
    auto-resolve turns for every unit that isn't the human-controlled one
    until it's their turn again or combat ends."""
    while True:
        encounter = get_encounter(encounter_id)
        outcome = _check_outcome(encounter["units"])
        if outcome != "active":
            conn.execute("UPDATE combat_encounters SET status=? WHERE id=?", (outcome, encounter_id))
            return
        order = encounter["turn_order"]
        by_id = {u["id"]: u for u in encounter["units"]}
        n = len(order)
        idx = encounter["turn_index"]
        found = False
        for _ in range(n):
            idx = (idx + 1) % n
            if by_id[order[idx]]["is_active"]:
                found = True
                break
        if not found:
            conn.execute("UPDATE combat_encounters SET status='lost' WHERE id=?", (encounter_id,))
            return
        round_number = encounter["round_number"] + (1 if idx <= encounter["turn_index"] else 0)
        conn.execute("UPDATE combat_encounters SET turn_index=?, round_number=? WHERE id=?",
                     (idx, round_number, encounter_id))
        current_unit = by_id[order[idx]]
        if current_unit["stats"].get("is_human"):
            return  # human's turn -- stop and wait for a move/attack/cast/end-turn call
        # AI-controlled unit (ally or enemy): resolve its turn immediately
        encounter = get_encounter(encounter_id)
        unit = next(u for u in encounter["units"] if u["id"] == current_unit["id"])
        logs = _resolve_ai_unit_turn(conn, encounter, unit)
        _append_log(conn, encounter_id, logs)
        conn.commit()
        outcome = _check_outcome(get_encounter(encounter_id)["units"])
        if outcome != "active":
            conn.execute("UPDATE combat_encounters SET status=? WHERE id=?", (outcome, encounter_id))
            conn.commit()
            return


def _build_human_unit(conn, character_id: int | None, px: int, py: int) -> dict:
    from core.levelling import get_full_sheet

    sheet = get_full_sheet(character_id) if character_id else None
    if not sheet:
        stats = {"str_mod": 1, "dex_mod": 1, "con_mod": 1, "int_mod": 0, "wis_mod": 0, "cha_mod": 0,
                  "proficiency": 2, "ac": 11, "weapon_name": None, "weapon_tier": 2, "weapon_damage": "1d6",
                  "weapon_finesse_or_ranged": False, "known_spells": [], "spell_mod": 0,
                  "spell_ability": "intelligence", "feats": [], "character_id": character_id, "is_human": True}
        return {"unit_name": "Hero", "unit_type": "player", "hp": 30, "max_hp": 30, "x": px, "y": py,
                "initiative": random.randint(1, 20) + 1, "stats": stats}

    total = sheet.get("total_stats", {})

    def mod(key):
        return stat_mod((total.get(key) or {}).get("total"))

    str_mod, dex_mod, con_mod = mod("strength"), mod("dexterity"), mod("constitution")
    int_mod, wis_mod, cha_mod = mod("intelligence"), mod("wisdom"), mod("charisma_stat")
    level = sheet.get("calc_lv") or sheet.get("level") or 1
    proficiency = proficiency_bonus(level)
    max_hp = 20 + level * 8 + con_mod * level

    feats = [f for f in (sheet.get("traits") or []) if f in COMBAT_FEATS]
    armor_bonus = 1 if "Dual Wielder" in feats else 0
    weapon_name = None
    weapon_tier = 2
    for row in conn.execute(
        "SELECT item_name, item_type, stat_bonuses FROM inventory WHERE character_id=? AND equip_slot IS NOT NULL AND equip_slot != ''",
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
        weapon_data = _dnd_weapons.DND_WEAPONS[weapon_name]
        weapon_damage = weapon_data["damage"]
        finesse_or_ranged = _dnd_weapons.is_finesse_or_ranged(weapon_name)
    else:
        weapon_damage = _synthetic_weapon_damage(weapon_tier)
        finesse_or_ranged = False

    profession = sheet.get("profession", "")
    known_spells = [s for s in (sheet.get("spells") or []) if s in _spells.SPELLS]
    spell_ability = _spells.casting_ability_for(profession)
    spell_mod = {"intelligence": int_mod, "wisdom": wis_mod, "charisma_stat": cha_mod}.get(spell_ability, int_mod)

    ac = 10 + dex_mod + armor_bonus
    initiative = random.randint(1, 20) + dex_mod + (5 if "Alert" in feats else 0)

    stats = {"str_mod": str_mod, "dex_mod": dex_mod, "con_mod": con_mod,
              "int_mod": int_mod, "wis_mod": wis_mod, "cha_mod": cha_mod,
              "proficiency": proficiency, "ac": ac, "weapon_name": weapon_name, "weapon_tier": weapon_tier,
              "weapon_damage": weapon_damage, "weapon_finesse_or_ranged": finesse_or_ranged,
              "known_spells": known_spells, "spell_mod": spell_mod, "spell_ability": spell_ability,
              "feats": feats, "character_id": character_id, "is_human": True}
    return {"unit_name": sheet.get("name", "Hero"), "unit_type": "player", "hp": max_hp, "max_hp": max_hp,
            "x": px, "y": py, "initiative": initiative, "stats": stats}


def start_encounter(session_id: str, world_id: int | None, character_id: int | None, danger: int = 4) -> dict:
    conn = get_conn()
    width = height = GRID_SIZE
    exclude: set[tuple[int, int]] = set()
    units = []

    px, py = 1, height // 2
    exclude.add((px, py))
    units.append(_build_human_unit(conn, character_id, px, py))

    danger = max(0, min(10, danger))
    ai_proficiency = proficiency_bonus(2 + danger // 3)

    for ally_name, ax, ay_offset in ALLY_DEFS:
        pos = (ax, min(height - 1, max(0, py + ay_offset)))
        exclude.add(pos)
        units.append({"unit_name": ally_name, "unit_type": "player", "hp": 26, "max_hp": 26, "x": pos[0], "y": pos[1],
                      "initiative": random.randint(1, 20) + 1,
                      "stats": {"str_mod": 2, "dex_mod": 1, "con_mod": 1, "proficiency": 2, "ac": 12,
                                "weapon_name": None, "weapon_tier": 2, "weapon_damage": "1d6",
                                "weapon_finesse_or_ranged": False, "feats": [], "character_id": None}})

    enemy_count = 2 + min(3, danger // 3)
    enemy_hp = 14 + danger * 3
    for i in range(enemy_count):
        while True:
            pos = (random.randint(width - 3, width - 1), random.randint(0, height - 1))
            if pos not in exclude:
                break
        exclude.add(pos)
        e_dex = danger // 4
        e_tier = min(6, 2 + danger // 2)
        units.append({"unit_name": f"{random.choice(ENEMY_NAMES)} {i + 1}", "unit_type": "enemy",
                      "hp": enemy_hp, "max_hp": enemy_hp, "x": pos[0], "y": pos[1],
                      "initiative": random.randint(1, 20) + e_dex,
                      "stats": {"str_mod": 1 + danger // 3, "dex_mod": e_dex, "con_mod": danger // 4,
                                "proficiency": ai_proficiency, "ac": 10 + e_dex + danger // 5,
                                "weapon_name": None, "weapon_tier": e_tier, "weapon_damage": _synthetic_weapon_damage(e_tier),
                                "weapon_finesse_or_ranged": False, "feats": [], "character_id": None}})

    obstacles = _random_obstacles(width, height, random.randint(5, 8), exclude)

    cur = conn.execute(
        "INSERT INTO combat_encounters (session_id,world_id,character_id,grid_width,grid_height,obstacles_json,"
        "turn_order_json,turn_index,round_number,status,log_json,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (session_id, world_id, character_id, width, height, json.dumps([list(o) for o in obstacles]),
         "[]", 0, 1, "active", json.dumps([f"Combat begins! {enemy_count} {'enemy' if enemy_count == 1 else 'enemies'} emerge."]),
         now_iso()),
    )
    encounter_id = cur.lastrowid

    unit_ids = []
    for u in units:
        cur2 = conn.execute(
            "INSERT INTO combat_state (session_id,unit_name,unit_type,hp,max_hp,x,y,status_effects,initiative,is_active,encounter_id,stats_json) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (session_id, u["unit_name"], u["unit_type"], u["hp"], u["max_hp"], u["x"], u["y"], "[]",
             u["initiative"], 1, encounter_id, json.dumps(u["stats"])),
        )
        unit_ids.append(cur2.lastrowid)

    order = [uid for uid, _ in sorted(zip(unit_ids, [u["initiative"] for u in units]), key=lambda pair: -pair[1])]
    conn.execute("UPDATE combat_encounters SET turn_order_json=? WHERE id=?", (json.dumps(order), encounter_id))
    conn.commit()

    # Turn 0 might belong to an AI unit -- resolve forward to the human's turn (or game over).
    by_id = {uid: u for uid, u in zip(unit_ids, units)}
    first_unit = by_id[order[0]]
    if not first_unit["stats"].get("is_human"):
        conn.execute("UPDATE combat_encounters SET turn_index=-1 WHERE id=?", (encounter_id,))
        conn.commit()
        _advance_turn(conn, encounter_id)
        conn.commit()
    conn.close()
    return get_encounter(encounter_id)


def get_active_encounter(session_id: str) -> dict | None:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id FROM combat_encounters WHERE session_id=? AND status='active' ORDER BY id DESC LIMIT 1",
            (session_id,)).fetchone()
    finally:
        conn.close()
    return get_encounter(row["id"]) if row else None


def _require_human_turn(encounter: dict, unit_id: int) -> dict | None:
    if encounter["status"] != "active":
        return {"error": "Combat has already ended."}
    if encounter["current_unit_id"] != unit_id:
        return {"error": "It's not that unit's turn."}
    return None


def move_unit(encounter_id: int, unit_id: int, x: int, y: int) -> dict:
    encounter = get_encounter(encounter_id)
    if not encounter:
        return {"error": "Encounter not found."}
    err = _require_human_turn(encounter, unit_id)
    if err:
        return err
    unit = next((u for u in encounter["units"] if u["id"] == unit_id), None)
    if not unit:
        return {"error": "Unit not found."}
    obstacles = set(encounter["obstacles"])
    occupied = {(u["x"], u["y"]) for u in encounter["units"] if u["is_active"] and u["id"] != unit_id}
    reachable = _bfs_reachable((unit["x"], unit["y"]), obstacles, occupied, encounter["grid_width"], encounter["grid_height"], MOVE_POINTS)
    if (x, y) not in reachable:
        return {"error": "That tile is out of movement range, blocked, or occupied."}
    conn = get_conn()
    try:
        conn.execute("UPDATE combat_state SET x=?, y=? WHERE id=?", (x, y, unit_id))
        _append_log(conn, encounter_id, [f"{unit['unit_name']} moves."])
        conn.commit()
        _advance_turn(conn, encounter_id)
        conn.commit()
    finally:
        conn.close()
    return get_encounter(encounter_id)


def attack_unit(encounter_id: int, unit_id: int, target_id: int, power_attack: bool = False) -> dict:
    encounter = get_encounter(encounter_id)
    if not encounter:
        return {"error": "Encounter not found."}
    err = _require_human_turn(encounter, unit_id)
    if err:
        return err
    unit = next((u for u in encounter["units"] if u["id"] == unit_id), None)
    target = next((u for u in encounter["units"] if u["id"] == target_id), None)
    if not unit or not target or not target["is_active"]:
        return {"error": "Invalid target."}
    if target["unit_type"] == unit["unit_type"]:
        return {"error": "That unit isn't an enemy."}
    dist = _chebyshev(unit["x"], unit["y"], target["x"], target["y"])
    rng = _weapon_range_for(unit["stats"].get("weapon_name"), unit["stats"].get("weapon_tier"))
    if dist > rng:
        return {"error": f"Target is out of range (range {rng}, distance {dist})."}
    obstacles = set(encounter["obstacles"])
    if rng > 1 and not _line_clear(obstacles, unit["x"], unit["y"], target["x"], target["y"]):
        return {"error": "An obstacle blocks the line of fire."}
    conn = get_conn()
    try:
        message = _resolve_attack(conn, unit, target, power_attack=power_attack)
        _append_log(conn, encounter_id, [message])
        conn.commit()
        outcome = _check_outcome(get_encounter(encounter_id)["units"])
        if outcome != "active":
            conn.execute("UPDATE combat_encounters SET status=? WHERE id=?", (outcome, encounter_id))
            conn.commit()
        else:
            _advance_turn(conn, encounter_id)
            conn.commit()
    finally:
        conn.close()
    return get_encounter(encounter_id)


def cast_spell(encounter_id: int, unit_id: int, spell_name: str, target_id: int | None = None) -> dict:
    encounter = get_encounter(encounter_id)
    if not encounter:
        return {"error": "Encounter not found."}
    err = _require_human_turn(encounter, unit_id)
    if err:
        return err
    caster = next((u for u in encounter["units"] if u["id"] == unit_id), None)
    if not caster:
        return {"error": "Unit not found."}
    if spell_name not in caster["stats"].get("known_spells", []):
        return {"error": "That spell isn't known by this character."}
    spell = _spells.SPELLS.get(spell_name)
    if not spell:
        return {"error": "Unknown spell."}
    target = next((u for u in encounter["units"] if u["id"] == target_id), None) if target_id else None
    if spell["effect_type"] in ("attack", "save"):
        if not target or not target["is_active"] or target["unit_type"] == caster["unit_type"]:
            return {"error": "That spell needs a living enemy target."}
    if spell["effect_type"] == "heal" and target and target["unit_type"] != caster["unit_type"]:
        return {"error": "You can only heal allies."}
    conn = get_conn()
    try:
        message = _resolve_spell(conn, caster, spell_name, target)
        _append_log(conn, encounter_id, [message])
        conn.commit()
        outcome = _check_outcome(get_encounter(encounter_id)["units"])
        if outcome != "active":
            conn.execute("UPDATE combat_encounters SET status=? WHERE id=?", (outcome, encounter_id))
            conn.commit()
        else:
            _advance_turn(conn, encounter_id)
            conn.commit()
    finally:
        conn.close()
    return get_encounter(encounter_id)


def end_turn(encounter_id: int, unit_id: int) -> dict:
    encounter = get_encounter(encounter_id)
    if not encounter:
        return {"error": "Encounter not found."}
    err = _require_human_turn(encounter, unit_id)
    if err:
        return err
    conn = get_conn()
    try:
        _append_log(conn, encounter_id, [f"{next(u for u in encounter['units'] if u['id'] == unit_id)['unit_name']} holds position."])
        conn.commit()
        _advance_turn(conn, encounter_id)
        conn.commit()
    finally:
        conn.close()
    return get_encounter(encounter_id)
