"""AiChat Pro v21 — Simulation Engine
NPC goal system, faction war simulation, supply-demand economy,
weather effects on gameplay, quest chain dependencies, AI director.
All systems operate per world tick."""
from __future__ import annotations
import json, random, math
from typing import Dict, List, Optional, Tuple
from core.storage import get_conn, now_iso

# ═══════════════════════════════════════════════════════════════
# NPC GOAL SYSTEM — 3 goals (survive, profit, loyalty) per NPC
# ═══════════════════════════════════════════════════════════════

NPC_ACTIVITIES = {
    "survive": ["Guard Post", "Patrol", "Rest", "Forage", "Seek Shelter", "Train"],
    "profit": ["Trade", "Craft", "Mine", "Farm", "Gamble", "Negotiate"],
    "loyalty": ["Report to Leader", "Attend Meeting", "Recruit", "Pray", "Celebrate", "Plan"],
}

def get_npc_current_goal(npc_id: int) -> str:
    """Determine NPC's dominant goal based on weights."""
    conn = get_conn()
    row = conn.execute("SELECT goal_survive, goal_profit, goal_loyalty FROM npcs WHERE id=?",
                       (npc_id,)).fetchone()
    conn.close()
    if not row:
        return "survive"
    goals = {"survive": row["goal_survive"] or 5,
             "profit": row["goal_profit"] or 5,
             "loyalty": row["goal_loyalty"] or 5}
    return max(goals, key=goals.get)

def update_npc_schedule_from_goals(npc_id: int, world_id: int):
    """Generate NPC daily schedule based on their dominant goal."""
    goal = get_npc_current_goal(npc_id)
    activities = NPC_ACTIVITIES.get(goal, NPC_ACTIVITIES["survive"])
    time_slots = ["dawn", "morning", "midday", "afternoon", "evening", "night", "midnight", "late_night"]
    schedule = {}
    for slot in time_slots:
        schedule[slot] = random.choice(activities)

    conn = get_conn()
    conn.execute("UPDATE npcs SET schedule_json=? WHERE id=?",
                 (json.dumps(schedule), npc_id))
    # Update existing schedule table too
    conn.execute("DELETE FROM npc_schedules WHERE npc_id=? AND world_id=?", (npc_id, world_id))
    for slot, activity in schedule.items():
        conn.execute("INSERT INTO npc_schedules (npc_id, world_id, time_slot, activity) VALUES (?,?,?,?)",
                     (npc_id, world_id, slot, activity))
    conn.commit()
    conn.close()

def adjust_npc_goals(npc_id: int, event: str):
    """Adjust NPC goals based on world events."""
    conn = get_conn()
    row = conn.execute("SELECT goal_survive, goal_profit, goal_loyalty FROM npcs WHERE id=?",
                       (npc_id,)).fetchone()
    if not row: conn.close(); return
    s, p, l = row["goal_survive"] or 5, row["goal_profit"] or 5, row["goal_loyalty"] or 5
    adjustments = {
        "war": (3, -1, 1), "peace": (-1, 2, 0), "famine": (3, -2, 0),
        "prosperity": (-1, 3, 0), "betrayal": (1, 0, -3), "festival": (-1, 1, 2),
        "plague": (4, -2, -1), "trade_boom": (0, 4, 0),
    }
    ds, dp, dl = adjustments.get(event, (0, 0, 0))
    s = max(1, min(10, s + ds))
    p = max(1, min(10, p + dp))
    l = max(1, min(10, l + dl))
    conn.execute("UPDATE npcs SET goal_survive=?, goal_profit=?, goal_loyalty=? WHERE id=?",
                 (s, p, l, npc_id))
    conn.commit(); conn.close()

# ═══════════════════════════════════════════════════════════════
# NPC MEMORY — NPCs remember player actions
# ═══════════════════════════════════════════════════════════════

def add_npc_memory(npc_id: int, memory_text: str, importance: int = 5):
    """Add a memory to an NPC. Max 20 memories per NPC."""
    conn = get_conn()
    row = conn.execute("SELECT memory_json FROM npcs WHERE id=?", (npc_id,)).fetchone()
    if not row: conn.close(); return
    memories = json.loads(row["memory_json"] or "[]")
    memories.append({"text": memory_text, "importance": importance, "when": now_iso()})
    # Keep top 20 by importance
    memories.sort(key=lambda m: m.get("importance", 0), reverse=True)
    memories = memories[:20]
    conn.execute("UPDATE npcs SET memory_json=? WHERE id=?", (json.dumps(memories), npc_id))
    conn.commit(); conn.close()

def get_npc_memories(npc_id: int) -> List[Dict]:
    conn = get_conn()
    row = conn.execute("SELECT memory_json FROM npcs WHERE id=?", (npc_id,)).fetchone()
    conn.close()
    if not row: return []
    return json.loads(row["memory_json"] or "[]")

def build_npc_prompt_context(npc_id: int) -> str:
    """Build NPC context for chat prompt with goals and memories."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM npcs WHERE id=?", (npc_id,)).fetchone()
    conn.close()
    if not row: return ""
    goal = get_npc_current_goal(npc_id)
    memories = get_npc_memories(npc_id)
    mem_text = "; ".join(m["text"] for m in memories[:5]) if memories else "No memories"
    return (f"[NPC {row['name']}: profession={row['profession']}, mood={row['mood']}, "
            f"current_goal={goal}, memories=({mem_text})]")

# ═══════════════════════════════════════════════════════════════
# FACTION WAR SIMULATION
# ═══════════════════════════════════════════════════════════════

def resolve_faction_war(world_id: int, attacker: str, defender: str) -> Dict:
    """Resolve a war between two factions. Returns battle result."""
    conn = get_conn()
    att = conn.execute("SELECT * FROM factions WHERE world_id=? AND name=?",
                       (world_id, attacker)).fetchone()
    dfd = conn.execute("SELECT * FROM factions WHERE world_id=? AND name=?",
                       (world_id, defender)).fetchone()
    if not att or not dfd:
        conn.close()
        return {"error": "Faction not found"}

    att_str = (att["military_strength"] or 100) + random.randint(-20, 20)
    def_str = (dfd["military_strength"] or 100) + random.randint(-20, 20)
    # Terrain bonus for defender
    def_str = int(def_str * 1.15)

    winner = attacker if att_str > def_str else defender
    loser = defender if winner == attacker else attacker
    territory_lost = None

    if winner == attacker and dfd["territory"]:
        territory_lost = dfd["territory"]
        # Transfer territory
        conn.execute("UPDATE factions SET territory=? WHERE world_id=? AND name=?",
                     (territory_lost, world_id, attacker))
        conn.execute("UPDATE factions SET territory=NULL WHERE world_id=? AND name=?",
                     (world_id, defender))

    # Casualties reduce military strength
    att_loss = random.randint(10, 30)
    def_loss = random.randint(15, 40)
    conn.execute("UPDATE factions SET military_strength=MAX(10, military_strength-?) WHERE world_id=? AND name=?",
                 (att_loss, world_id, attacker))
    conn.execute("UPDATE factions SET military_strength=MAX(10, military_strength-?) WHERE world_id=? AND name=?",
                 (def_loss, world_id, defender))

    # Log the war
    conn.execute("INSERT INTO faction_wars (world_id, attacker, defender, attacker_strength, "
                 "defender_strength, result, territory_changed, tick, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                 (world_id, attacker, defender, att_str, def_str, winner,
                  territory_lost or "", 0, now_iso()))
    conn.commit(); conn.close()

    return {"winner": winner, "loser": loser, "attacker_strength": att_str,
            "defender_strength": def_str, "territory_changed": territory_lost}

def check_war_triggers(world_id: int) -> Optional[Dict]:
    """Check if any faction relations have degraded enough to trigger war."""
    conn = get_conn()
    hostile = conn.execute(
        "SELECT faction_a, faction_b FROM diplomacy WHERE world_id=? AND relation='hostile'",
        (world_id,)).fetchall()
    conn.close()
    if hostile and random.random() < 0.15:  # 15% chance per hostile pair per tick
        pair = random.choice(hostile)
        return resolve_faction_war(world_id, pair["faction_a"], pair["faction_b"])
    return None

# ═══════════════════════════════════════════════════════════════
# SUPPLY-DEMAND ECONOMY
# ═══════════════════════════════════════════════════════════════

DEFAULT_GOODS = [
    ("Food", 100, 100, 5.0), ("Iron", 80, 60, 12.0), ("Wood", 120, 90, 3.0),
    ("Weapons", 30, 50, 25.0), ("Cloth", 70, 80, 8.0), ("Medicine", 40, 60, 15.0),
    ("Luxury", 20, 40, 50.0), ("Stone", 100, 70, 4.0),
]

def init_market(world_id: int):
    """Initialize market with default goods."""
    conn = get_conn()
    for item, supply, demand, price in DEFAULT_GOODS:
        conn.execute("INSERT OR IGNORE INTO market_prices (world_id, item, supply, demand, "
                     "base_price, current_price, updated_at) VALUES (?,?,?,?,?,?,?)",
                     (world_id, item, supply, demand, price, price, now_iso()))
    conn.commit(); conn.close()

def tick_economy(world_id: int, weather: str = "clear"):
    """Advance economy one tick. Weather affects food/resource production."""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM market_prices WHERE world_id=?", (world_id,)).fetchall()

    weather_modifiers = {
        "clear": 1.0, "rain": 0.9, "storm": 0.6, "snow": 0.7,
        "drought": 0.4, "blizzard": 0.3, "fog": 0.85, "heatwave": 0.75,
    }
    w_mod = weather_modifiers.get(weather, 1.0)

    for row in rows:
        supply = row["supply"]
        demand = row["demand"]

        # Random fluctuation
        supply += random.randint(-10, 15)
        demand += random.randint(-10, 15)

        # Weather affects food supply
        if row["item"] == "Food":
            supply = int(supply * w_mod)
        elif row["item"] in ("Wood", "Stone", "Iron"):
            supply = int(supply * max(0.7, w_mod))

        supply = max(10, supply)
        demand = max(10, demand)

        # Price = base_price * (demand / supply)
        price = row["base_price"] * (demand / max(supply, 1))
        price = round(max(1.0, min(price, row["base_price"] * 5)), 2)

        conn.execute("UPDATE market_prices SET supply=?, demand=?, current_price=?, updated_at=? "
                     "WHERE id=?", (supply, demand, price, now_iso(), row["id"]))
    conn.commit(); conn.close()

def get_market(world_id: int) -> List[Dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM market_prices WHERE world_id=? ORDER BY item", (world_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ═══════════════════════════════════════════════════════════════
# WEATHER EFFECTS ON GAMEPLAY
# ═══════════════════════════════════════════════════════════════

WEATHER_EFFECTS = {
    "clear":    {"travel_blocked": False, "food_mod": 1.0,  "army_mod": 1.0},
    "rain":     {"travel_blocked": False, "food_mod": 1.1,  "army_mod": 0.9},
    "storm":    {"travel_blocked": True,  "food_mod": 0.7,  "army_mod": 0.6},
    "snow":     {"travel_blocked": False, "food_mod": 0.8,  "army_mod": 0.7},
    "blizzard": {"travel_blocked": True,  "food_mod": 0.4,  "army_mod": 0.3},
    "drought":  {"travel_blocked": False, "food_mod": 0.4,  "army_mod": 0.9},
    "fog":      {"travel_blocked": False, "food_mod": 1.0,  "army_mod": 0.8},
    "heatwave": {"travel_blocked": False, "food_mod": 0.6,  "army_mod": 0.8},
}

def get_weather_effects(weather: str) -> Dict:
    return WEATHER_EFFECTS.get(weather, WEATHER_EFFECTS["clear"])

def log_weather(world_id: int, tick: int, weather: str, temperature: str):
    effects = get_weather_effects(weather)
    conn = get_conn()
    conn.execute("INSERT INTO world_weather_log (world_id, tick, weather, temperature, "
                 "travel_blocked, food_modifier, army_modifier, created_at) VALUES (?,?,?,?,?,?,?,?)",
                 (world_id, tick, weather, temperature,
                  1 if effects["travel_blocked"] else 0,
                  effects["food_mod"], effects["army_mod"], now_iso()))
    conn.commit(); conn.close()

# ═══════════════════════════════════════════════════════════════
# QUEST CHAIN DEPENDENCIES
# ═══════════════════════════════════════════════════════════════

def create_quest_chain(character_name: str, chain: List[Dict]) -> str:
    """Create a chain of dependent quests. Each dict: {title, description, quest_type, reward}.
    Returns chain_id."""
    import hashlib
    chain_id = hashlib.md5(f"{character_name}_{now_iso()}".encode()).hexdigest()[:12]
    conn = get_conn()
    prev_id = None
    for q in chain:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO quests (character_name, quest_type, title, description, reward, "
            "depends_on, chain_id, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (character_name, q.get("quest_type", "story"), q["title"], q["description"],
             q.get("reward", "50 XP"), prev_id, chain_id, now_iso()))
        prev_id = cur.lastrowid
    conn.commit(); conn.close()
    return chain_id

def get_available_quests(character_name: str) -> List[Dict]:
    """Get quests that are available (dependencies met)."""
    conn = get_conn()
    all_quests = conn.execute(
        "SELECT * FROM quests WHERE character_name=? AND status='active'",
        (character_name,)).fetchall()
    conn.close()
    available = []
    for q in all_quests:
        dep = q["depends_on"]
        if dep is None:
            available.append(dict(q))
        else:
            # Check if dependency is completed
            conn2 = get_conn()
            dep_row = conn2.execute("SELECT status FROM quests WHERE id=?", (dep,)).fetchone()
            conn2.close()
            if dep_row and dep_row["status"] == "completed":
                available.append(dict(q))
    return available

def complete_chain_quest(quest_id: int) -> Optional[Dict]:
    """Complete a quest and check if next in chain is unlocked."""
    conn = get_conn()
    conn.execute("UPDATE quests SET status='completed', progress=100 WHERE id=?", (quest_id,))
    # Check for next quest in chain
    next_q = conn.execute("SELECT * FROM quests WHERE depends_on=? AND status='active'",
                          (quest_id,)).fetchone()
    conn.commit(); conn.close()
    return dict(next_q) if next_q else None

# ═══════════════════════════════════════════════════════════════
# AI DIRECTOR — adjusts difficulty dynamically
# ═══════════════════════════════════════════════════════════════

def get_director_state(world_id: int) -> Dict:
    conn = get_conn()
    row = conn.execute("SELECT * FROM ai_director WHERE world_id=? ORDER BY id DESC LIMIT 1",
                       (world_id,)).fetchone()
    conn.close()
    if row: return dict(row)
    return {"difficulty_level": 5, "threat_level": 50, "player_power": 10}

def update_director(world_id: int, player_level: int = 1, recent_wins: int = 0,
                    recent_losses: int = 0):
    """AI director adjusts difficulty based on player performance."""
    state = get_director_state(world_id)
    difficulty = state["difficulty_level"]
    threat = state["threat_level"]

    # If player keeps winning, increase difficulty
    if recent_wins > 3:
        difficulty = min(10, difficulty + 1)
        threat = min(100, threat + 10)
    elif recent_losses > 2:
        difficulty = max(1, difficulty - 1)
        threat = max(10, threat - 15)

    # Scale with player level
    player_power = player_level * 5 + recent_wins * 3
    threat = max(10, min(100, int(player_power * 0.8 + random.randint(-10, 10))))

    conn = get_conn()
    conn.execute("INSERT INTO ai_director (world_id, difficulty_level, threat_level, "
                 "player_power, last_adjusted) VALUES (?,?,?,?,?)",
                 (world_id, difficulty, threat, player_power, now_iso()))
    conn.commit(); conn.close()
    return {"difficulty_level": difficulty, "threat_level": threat, "player_power": player_power}

def generate_scaled_encounter(world_id: int) -> Dict:
    """Generate an encounter scaled to current AI director difficulty."""
    state = get_director_state(world_id)
    diff = state["difficulty_level"]

    enemy_count = max(1, min(5, diff // 2))
    base_hp = 30 + diff * 15
    base_str = 5 + diff * 3
    names = ["Goblin", "Bandit", "Wolf", "Skeleton", "Orc", "Dark Knight",
             "Troll", "Wraith", "Drake", "Demon"]

    enemies = []
    for i in range(enemy_count):
        tier = min(len(names) - 1, diff - 1 + random.randint(-1, 1))
        tier = max(0, tier)
        enemies.append({
            "name": f"{names[tier]}" + (f" #{i+1}" if enemy_count > 1 else ""),
            "hp": base_hp + random.randint(-10, 20),
            "strength": base_str + random.randint(-2, 3),
            "is_boss": diff >= 8 and i == 0,
        })
    return {"enemies": enemies, "difficulty": diff, "threat": state["threat_level"]}

# ═══════════════════════════════════════════════════════════════
# MASTER TICK — runs all simulation systems for one world tick
# ═══════════════════════════════════════════════════════════════

def run_world_simulation_tick(world_id: int) -> Dict:
    """Run one full simulation tick for a world. Returns summary of events."""
    events = []
    conn = get_conn()
    world = conn.execute("SELECT * FROM worlds WHERE id=?", (world_id,)).fetchone()
    if not world:
        conn.close()
        return {"events": ["World not found"]}

    weather = world["weather"] or "clear"
    tick = (world["world_tick"] or 0)

    # 1. Weather effects
    w_effects = get_weather_effects(weather)
    log_weather(world_id, tick, weather, world["temperature"] or "mild")

    # 2. Economy tick
    tick_economy(world_id, weather)
    events.append(f"Economy updated (weather: {weather})")

    # 3. NPC goal-driven schedules
    npcs = conn.execute("SELECT id FROM npcs WHERE world_id=?", (world_id,)).fetchall()
    for npc in npcs:
        update_npc_schedule_from_goals(npc["id"], world_id)
    if npcs:
        events.append(f"{len(npcs)} NPCs updated schedules")

    # 4. Faction war check
    war_result = check_war_triggers(world_id)
    if war_result and "winner" in war_result:
        events.append(f"⚔️ War! {war_result['winner']} defeated {war_result['loser']}")

    # 5. Faction strength recovery
    factions = conn.execute("SELECT id, military_strength FROM factions WHERE world_id=?",
                            (world_id,)).fetchall()
    for f in factions:
        recovery = random.randint(1, 5)
        new_str = min(200, (f["military_strength"] or 100) + recovery)
        conn.execute("UPDATE factions SET military_strength=? WHERE id=?", (new_str, f["id"]))

    conn.commit(); conn.close()

    return {"events": events, "weather_effects": w_effects}
