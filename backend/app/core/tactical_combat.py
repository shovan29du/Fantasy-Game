"""Turn-based tactical combat on an 8x8 grid board -- obstacles, initiative
order, and one move-or-attack action per turn. Enemy and ally units resolve
their own turns automatically (simple "close the distance, then swing"
AI); the frontend only ever needs to act for the one human-controlled unit.
"""
from __future__ import annotations

import json
import random
from collections import deque

from core.storage import get_conn, now_iso
from core.logging_setup import get_logger
from backend.app.domain import weapons as _weapons

log = get_logger(__name__)

GRID_SIZE = 8
MOVE_POINTS = 3
BASE_DEFENSE = 10
ENEMY_NAMES = ["Raider", "Cultist", "Marauder", "Feral Beast", "Drone", "Ghoul", "Bandit", "Wraith"]
ALLY_DEFS = [("Kael Ironroot", 2, -2), ("Seraphine", 2, 2)]  # (name, x, y-offset from player row)


def stat_mod(value: int | None) -> int:
    return ((value or 10) - 10) // 2


def _weapon_range(tier: int | None) -> int:
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


def _resolve_attack(conn, attacker: dict, defender: dict) -> str:
    roll = random.randint(1, 20)
    crit = roll == 20
    attack_total = roll + attacker["stats"].get("str_mod", 0)
    defense_total = BASE_DEFENSE + defender["stats"].get("con_mod", 0)
    hit = crit or attack_total >= defense_total
    if not hit:
        return f"{attacker['unit_name']} attacks {defender['unit_name']} but misses."
    dmg = random.randint(1, 6) + max(0, attacker["stats"].get("str_mod", 0)) + attacker["stats"].get("weapon_tier", 2) // 2
    if crit:
        dmg *= 2
    new_hp = max(0, defender["hp"] - dmg)
    conn.execute("UPDATE combat_state SET hp=?, is_active=? WHERE id=?", (new_hp, 1 if new_hp > 0 else 0, defender["id"]))
    defender["hp"] = new_hp
    if new_hp <= 0:
        defender["is_active"] = 0
        return f"{attacker['unit_name']} hits {defender['unit_name']} for {dmg} damage{' (critical!)' if crit else ''} -- {defender['unit_name']} is defeated!"
    return f"{attacker['unit_name']} hits {defender['unit_name']} for {dmg} damage{' (critical!)' if crit else ''}."


def _resolve_ai_unit_turn(conn, encounter: dict, unit: dict) -> list[str]:
    units = encounter["units"]
    opposing_type = "enemy" if unit["unit_type"] == "player" else "player"
    targets = [u for u in units if u["unit_type"] == opposing_type and u["is_active"]]
    if not targets:
        return []
    target = min(targets, key=lambda t: _chebyshev(unit["x"], unit["y"], t["x"], t["y"]))
    dist = _chebyshev(unit["x"], unit["y"], target["x"], target["y"])
    rng = _weapon_range(unit["stats"].get("weapon_tier"))
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
            return  # human's turn -- stop and wait for a move/attack/end-turn call
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


def start_encounter(session_id: str, world_id: int | None, character_id: int | None, danger: int = 4) -> dict:
    from core.levelling import get_full_sheet

    conn = get_conn()
    width = height = GRID_SIZE
    exclude: set[tuple[int, int]] = set()
    units = []

    px, py = 1, height // 2
    exclude.add((px, py))
    sheet = get_full_sheet(character_id) if character_id else None
    if sheet:
        total = sheet.get("total_stats", {})
        str_mod = stat_mod((total.get("strength") or {}).get("total"))
        con_mod = stat_mod((total.get("constitution") or {}).get("total"))
        dex_mod = stat_mod((total.get("dexterity") or {}).get("total"))
        level = sheet.get("calc_lv") or sheet.get("level") or 1
        max_hp = 20 + level * 8 + con_mod * level
        weapon_tier = 2
        for row in conn.execute("SELECT stat_bonuses FROM inventory WHERE character_id=? AND equip_slot IS NOT NULL AND equip_slot != ''", (character_id,)).fetchall():
            try:
                bonuses = json.loads(row["stat_bonuses"] or "{}")
                if "weapon_tier" in bonuses:
                    weapon_tier = max(weapon_tier, bonuses["weapon_tier"])
            except Exception:
                pass
        name = sheet.get("name", "Hero")
    else:
        str_mod = con_mod = dex_mod = 1
        max_hp = 30
        weapon_tier = 2
        name = "Hero"
    units.append({"unit_name": name, "unit_type": "player", "hp": max_hp, "max_hp": max_hp, "x": px, "y": py,
                  "initiative": random.randint(1, 20) + dex_mod,
                  "stats": {"str_mod": str_mod, "con_mod": con_mod, "dex_mod": dex_mod,
                            "weapon_tier": weapon_tier, "character_id": character_id, "is_human": True}})

    for ally_name, ax, ay_offset in ALLY_DEFS:
        pos = (ax, min(height - 1, max(0, py + ay_offset)))
        exclude.add(pos)
        units.append({"unit_name": ally_name, "unit_type": "player", "hp": 26, "max_hp": 26, "x": pos[0], "y": pos[1],
                      "initiative": random.randint(1, 20) + 1,
                      "stats": {"str_mod": 2, "con_mod": 1, "dex_mod": 1, "weapon_tier": 2, "character_id": None}})

    danger = max(0, min(10, danger))
    enemy_count = 2 + min(3, danger // 3)
    enemy_hp = 14 + danger * 3
    for i in range(enemy_count):
        while True:
            pos = (random.randint(width - 3, width - 1), random.randint(0, height - 1))
            if pos not in exclude:
                break
        exclude.add(pos)
        units.append({"unit_name": f"{random.choice(ENEMY_NAMES)} {i + 1}", "unit_type": "enemy",
                      "hp": enemy_hp, "max_hp": enemy_hp, "x": pos[0], "y": pos[1],
                      "initiative": random.randint(1, 20) + danger // 4,
                      "stats": {"str_mod": 1 + danger // 3, "con_mod": danger // 4, "dex_mod": danger // 4,
                                "weapon_tier": min(6, 2 + danger // 2), "character_id": None}})

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


def attack_unit(encounter_id: int, unit_id: int, target_id: int) -> dict:
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
    rng = _weapon_range(unit["stats"].get("weapon_tier"))
    if dist > rng:
        return {"error": f"Target is out of range (range {rng}, distance {dist})."}
    obstacles = set(encounter["obstacles"])
    if rng > 1 and not _line_clear(obstacles, unit["x"], unit["y"], target["x"], target["y"]):
        return {"error": "An obstacle blocks the line of fire."}
    conn = get_conn()
    try:
        message = _resolve_attack(conn, unit, target)
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
