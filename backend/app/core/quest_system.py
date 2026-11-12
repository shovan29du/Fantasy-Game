"""AiChat Pro — Quest System with XP and Rich Rewards"""

from core.logging_setup import get_logger

log = get_logger(__name__)
import json, random, re
from core.storage import get_conn, now_iso

QUEST_TYPES = ["story","daily","bond","skill","exploration","combat","delivery","investigation","random"]
_QXP = {"story":200,"daily":30,"bond":60,"skill":50,"exploration":70,"combat":100,"delivery":40,"investigation":80,"random":40}
HINTS = ["Check last conversation.","Explore a different area.","Talk to an NPC.","Use a special ability.","Review your backstory.","Try diplomacy.","Check inventory."]

# Rich reward pools per quest type
_REWARD_POOL = {
    "story":        ["feat","spell","companion","plot_item","ally","title","stat_point","skill"],
    "daily":        ["gold","item","stat_point"],
    "bond":         ["companion","ally","stat_point","gold","item"],
    "skill":        ["skill","stat_point","item","spell"],
    "exploration":  ["item","spell","stat_point","plot_item","map_fragment"],
    "combat":       ["stat_point","feat","skill","item","gold"],
    "delivery":     ["gold","item","ally"],
    "investigation":["spell","skill","plot_item","item","feat"],
    "random":       ["gold","item","stat_point","skill","spell"],
}

_COMPANION_NAMES = ["Loyal Squire","Wise Mage","Stealthy Scout","Battle Cleric","Skilled Artisan","Wandering Bard","Veteran Guard","Hedge Witch"]
_PLOT_ITEMS = ["Ancient Map Fragment","Sealed Letter of Power","Enchanted Focusing Gem","Mysterious Iron Key","Prophet's Medallion","Faction Insignia","Runic Stone Tablet","Cursed Locket"]
_ALLY_NAMES = ["Local Guard Captain","Traveling Merchant Guild","Scholarly Brotherhood","Thieves' Ringleader","Noble House Steward","Rebel Leader"]
_TITLES = ["Hero of the Realm","Defender of the Weak","Shadow Walker","Arcane Scholar","Battle-Forged Warrior","Chosen of Fate","Guardian of the Light","Silver Tongue"]
_STAT_CHOICES = ["strength","dexterity","intelligence","wisdom","constitution","speed","luck","charisma_stat"]
_ITEM_REWARDS = ["Health Potion","Elixir of Strength","Scroll of Fireball","Fine Steel Sword","Enchanted Bow","Mage's Staff","Rogue's Daggers","Plate Gauntlets","Ring of Protection","Cloak of Shadows"]


def _pick_reward(quest_type: str, char_level: int = 1) -> dict:
    """Pick a rich reward based on quest type and character level."""
    pool = _REWARD_POOL.get(quest_type, _REWARD_POOL["random"])
    # Story quests at higher levels lean toward feats/companions
    if quest_type == "story" and char_level >= 5:
        pool = ["feat","companion","ally","title","plot_item"] + pool
    rtype = random.choice(pool)

    if rtype == "gold":
        amount = random.randint(20, 80) * max(1, char_level // 2)
        return {"type":"gold","amount":amount,"label":f"{amount} Gold","icon":"💰"}
    elif rtype == "stat_point":
        stat = random.choice(_STAT_CHOICES)
        return {"type":"stat_point","stat":stat,"amount":1,"label":f"+1 {stat.replace('_stat','').title()}","icon":"⬆"}
    elif rtype == "feat":
        from core.levelling import DND_FEATS
        available = list(DND_FEATS.keys())
        feat = random.choice(available)
        return {"type":"feat","feat":feat,"label":f"Feat: {feat}","icon":"⭐","desc":DND_FEATS[feat].get("desc","")}
    elif rtype == "spell":
        try:
            from backend.app.domain.spells import SPELLS
            spell = random.choice(list(SPELLS.keys()))
            return {"type":"spell","spell":spell,"label":f"Spell: {spell}","icon":"✨"}
        except Exception:
            return {"type":"item","item":"Spell Scroll","label":"Spell Scroll","icon":"📜"}
    elif rtype == "skill":
        from core.levelling import SKILL_TREES
        cat = random.choice(list(SKILL_TREES.keys()))
        tier = "tier1" if char_level < 5 else "tier2" if char_level < 10 else "tier3"
        skills = SKILL_TREES[cat].get(tier, SKILL_TREES[cat]["tier1"])
        skill = random.choice(skills)
        return {"type":"skill","skill":skill,"category":cat,"label":f"Skill: {skill}","icon":"🔮"}
    elif rtype == "companion":
        name = random.choice(_COMPANION_NAMES)
        return {"type":"companion","name":name,"label":f"Companion: {name}","icon":"👥"}
    elif rtype == "plot_item":
        item = random.choice(_PLOT_ITEMS)
        return {"type":"plot_item","item":item,"label":f"Plot Item: {item}","icon":"📦","rarity":"rare"}
    elif rtype == "ally":
        ally = random.choice(_ALLY_NAMES)
        return {"type":"ally","name":ally,"label":f"Ally: {ally}","icon":"🤝"}
    elif rtype == "title":
        title = random.choice(_TITLES)
        return {"type":"title","title":title,"label":f"Title: {title}","icon":"👑"}
    elif rtype == "map_fragment":
        return {"type":"plot_item","item":"Map Fragment","label":"Map Fragment","icon":"🗺","rarity":"uncommon"}
    else:
        item = random.choice(_ITEM_REWARDS)
        return {"type":"item","item":item,"label":item,"icon":"⚔"}


def _grant_reward(char_id: int, char_name: str, reward: dict):
    """Actually apply the reward to the character."""
    rtype = reward.get("type")
    try:
        if rtype == "gold":
            conn = get_conn()
            # Try economy table first, else add to inventory
            try:
                conn.execute("UPDATE economy SET gold=gold+? WHERE character_id=?", (reward["amount"], char_id))
                if conn.execute("SELECT changes()").fetchone()[0] == 0:
                    conn.execute("INSERT INTO economy (character_id, gold) VALUES (?,?)", (char_id, reward["amount"]))
            except Exception:
                conn.execute("INSERT INTO inventory (character_id,item_name,item_type,quantity,value,source,created_at) VALUES (?,?,?,?,?,?,?)",
                    (char_id, f"{reward['amount']} Gold", "currency", 1, reward["amount"], "quest", now_iso()))
            conn.commit(); conn.close()
        elif rtype == "stat_point":
            from core.levelling import increase_stat
            increase_stat(char_id, reward["stat"], reward.get("amount", 1))
        elif rtype == "feat":
            from core.levelling import add_feat_to_character
            add_feat_to_character(char_id, reward["feat"])
        elif rtype == "spell":
            from core.levelling import add_spell_to_character
            add_spell_to_character(char_id, reward["spell"])
        elif rtype == "skill":
            from core.levelling import add_skill_to_character
            add_skill_to_character(char_id, reward["skill"])
        elif rtype in ("companion","ally","plot_item","title","item"):
            conn = get_conn()
            conn.execute("INSERT INTO inventory (character_id,item_name,item_type,quantity,value,source,created_at) VALUES (?,?,?,?,?,?,?)",
                (char_id, reward.get("item") or reward.get("name") or reward.get("title","Reward"),
                 rtype, 1, 0, "quest", now_iso()))
            conn.commit(); conn.close()
    except Exception:
        log.debug("Failed to grant reward %s to char %s", rtype, char_id, exc_info=True)


def generate_quest(char_name, qtype="random", scenario="", title="", character_id=None):
    """Templated quest — always available, no LLM call."""
    if qtype == "random": qtype = random.choice(QUEST_TYPES[:-1])
    if not title: title = f"{qtype.title()} Quest for {char_name}"
    xp = _QXP.get(qtype, 40)
    reward = _pick_reward(qtype)
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO quests (character_id,character_name,quest_type,title,description,reward,hint,progress,status,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (character_id, char_name, qtype, title, f"Complete a {qtype} challenge: {scenario or 'current world'}.",
         reward["label"], random.choice(HINTS), 0, "active", now_iso()))
    qid = cur.lastrowid; conn.commit(); conn.close()
    return {"id": qid, "title": title, "type": qtype, "xp": xp, "reward_data": reward}


def _extract_json_object(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match: return None
    try: return json.loads(match.group(0))
    except json.JSONDecodeError: return None


def generate_dynamic_quest(char_name, history=None, world=None, character=None, qtype="random"):
    """Generate a quest tied to actual conversation history via LLM. Falls back to templated."""
    if qtype == "random": qtype = random.choice(QUEST_TYPES[:-1])
    xp = _QXP.get(qtype, 40)
    char_level = (character or {}).get("level", 1) or 1
    character_id = (character or {}).get("id")
    reward = _pick_reward(qtype, char_level)

    try:
        from core.chat_engine import send_to_llm
        recent = history[-12:] if history else []
        convo = "\n".join(f"{m.get('role','?')}: {m.get('content','')[:220]}" for m in recent) or "(no conversation yet)"
        world_line = f"World: {world.get('name','')}, {world.get('time_of_day','')}, {world.get('weather','')}." if world else ""
        char_line = f"Character: {char_name}" + (f", {character.get('profession','')}, Level {char_level}" if character else "") + "."

        prompt = (
            f"You are a quest designer for an ongoing interactive roleplay. Invent ONE {qtype} quest "
            f"that grows naturally out of what has actually happened in the conversation below — "
            f"reference specific names, places, items, or events that were actually mentioned. Do not "
            f"invent a generic fetch quest disconnected from the story.\n\n"
            f"{char_line} {world_line}\n\nRecent conversation:\n{convo}\n\n"
            f"Respond with ONLY a single JSON object, no other text, no markdown fences:\n"
            f'{{"title": "under 12 words", "description": "2-4 sentences, specific to the story above", '
            f'"hint": "one sentence hint"}}'
        )
        raw = send_to_llm([{"role": "system", "content": prompt}], temperature=0.85, max_tokens=300)
        data = _extract_json_object(raw)
        if not data or not data.get("title") or not data.get("description"):
            raise ValueError(f"Unparseable quest response: {raw[:200]!r}")

        title = str(data["title"])[:120]
        description = str(data["description"])[:600]
        hint = str(data.get("hint", "") or random.choice(HINTS))[:200]

        conn = get_conn()
        cur = conn.execute(
            "INSERT INTO quests (character_id,character_name,quest_type,title,description,reward,hint,progress,status,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (character_id, char_name, qtype, title, description, reward["label"], hint, 0, "active", now_iso()))
        qid = cur.lastrowid; conn.commit(); conn.close()
        return {"id": qid, "title": title, "type": qtype, "xp": xp, "dynamic": True, "reward_data": reward}
    except Exception:
        log.info("Dynamic quest generation failed for %s; using templated fallback", char_name, exc_info=True)
        result = generate_quest(char_name, qtype=qtype, character_id=character_id)
        result["dynamic"] = False
        return result


def complete_quest(qid, character_id: int | None = None):
    """Complete quest, award XP, pick and grant rich reward. Returns full reward details."""
    conn = get_conn()
    conn.execute("UPDATE quests SET progress=100,status='completed' WHERE id=?", (qid,))
    conn.commit()
    r = conn.execute("SELECT character_id,character_name,quest_type FROM quests WHERE id=?", (qid,)).fetchone()
    conn.close()
    if not r: return {}

    xp = _QXP.get(r["quest_type"], 40)

    # Resolve character
    char_id = character_id or r["character_id"]
    char_level = 1
    try:
        from core.levelling import get_character, get_character_by_name
        ch = get_character(char_id) if char_id else get_character_by_name(r["character_name"])
        if ch: char_id = ch["id"]; char_level = ch.get("level", 1) or 1
    except Exception:
        log.debug("Could not resolve character", exc_info=True)

    # Award XP and check level-up
    xp_result = {}
    try:
        from core.levelling import award_xp
        if char_id:
            xp_result = award_xp(char_id, xp, f"Quest #{qid} complete")
    except Exception:
        log.debug("XP award failed", exc_info=True)

    # Pick rich reward
    reward = _pick_reward(r["quest_type"], char_level)

    # Grant reward
    if char_id:
        _grant_reward(char_id, r["character_name"], reward)

    # Record relationship
    try:
        from core.relationship_engine import record_interaction
        record_interaction(r["character_name"], "quest_complete", f"Quest #{qid}")
    except Exception:
        log.debug("relationship record failed", exc_info=True)

    return {
        "quest_id": qid,
        "xp_awarded": xp,
        "reward": reward,
        "levelled_up": xp_result.get("levelled_up", False),
        "new_level": xp_result.get("new_level"),
        "level_up_choices": xp_result.get("level_up_choices"),
        **xp_result,
    }


def update_progress(qid, prog):
    conn = get_conn()
    conn.execute("UPDATE quests SET progress=?,status=? WHERE id=?",
        (min(prog, 100), "completed" if prog >= 100 else "active", qid))
    conn.commit(); conn.close()
    if prog >= 100: return complete_quest(qid)
    return {}


def _owner_clause(char_name, character_id):
    """Match a character's quests by id; name is only a fallback for quests
    that have no owning character row."""
    if character_id:
        return "(character_id=? OR (character_id IS NULL AND character_name=?))", [character_id, char_name]
    if char_name:
        return "character_name=?", [char_name]
    return "1=1", []


def get_active_quests(char_name="", character_id=None):
    where, params = _owner_clause(char_name, character_id)
    conn = get_conn()
    rows = conn.execute(f"SELECT * FROM quests WHERE {where} AND status='active' ORDER BY id DESC", params).fetchall()
    conn.close(); return [dict(r) for r in rows]


def get_all_quests(limit=100):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM quests ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close(); return [dict(r) for r in rows]


def abandon_quest(qid):
    conn = get_conn()
    conn.execute("UPDATE quests SET status='abandoned' WHERE id=?", (qid,))
    conn.commit(); conn.close()


def get_quest_history(char_name="", limit=20, character_id=None):
    where, params = _owner_clause(char_name, character_id)
    conn = get_conn()
    rows = conn.execute(
        f"SELECT * FROM quests WHERE {where} AND status IN ('completed','abandoned') ORDER BY id DESC LIMIT ?",
        (*params, limit)).fetchall()
    conn.close(); return [dict(r) for r in rows]
