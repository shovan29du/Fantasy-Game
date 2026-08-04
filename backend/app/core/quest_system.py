"""AiChat Pro — Quest System with XP"""

from core.logging_setup import get_logger

log = get_logger(__name__)
import json, random, re
from core.storage import get_conn, now_iso
QUEST_TYPES=["story","daily","bond","skill","exploration","combat","delivery","investigation","random"]
_QXP={"story":100,"daily":20,"bond":40,"skill":30,"exploration":35,"combat":60,"delivery":25,"investigation":45,"random":25}
REWARDS=["Gold +50","New Skill","Reputation +10","New Item","Trust +5","Achievement","Property","Follower"]
HINTS=["Check last conversation.","Explore a different area.","Talk to an NPC.","Use a special ability.","Review your backstory.","Try diplomacy.","Check inventory."]

def generate_quest(char_name, qtype="random", scenario="", title=""):
    """Templated quest -- always available, no LLM call. Used as the fallback
    for generate_dynamic_quest() and anywhere a guaranteed-fast quest is needed."""
    if qtype=="random": qtype=random.choice(QUEST_TYPES[:-1])
    if not title: title=f"{qtype.title()} Quest for {char_name}"
    xp=_QXP.get(qtype,25)
    conn=get_conn()
    cur=conn.execute("INSERT INTO quests (character_name,quest_type,title,description,reward,hint,progress,status,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (char_name,qtype,title,f"Complete a {qtype} challenge: {scenario or 'current world'}.",f"{random.choice(REWARDS)} | XP +{xp}",random.choice(HINTS),0,"active",now_iso()))
    qid=cur.lastrowid; conn.commit(); conn.close()
    return {"id":qid,"title":title,"type":qtype,"xp":xp}


def _extract_json_object(text: str):
    """Pull the first {...} block out of an LLM response and parse it."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def generate_dynamic_quest(char_name, history=None, world=None, character=None, qtype="random"):
    """Generate a quest tied to what's actually happened in this conversation,
    by asking the local LLM to invent one from recent chat history. Falls back
    to generate_quest() (templated, no LLM call) if the model is unreachable
    or returns something unparseable -- this must never raise or block chat."""
    if qtype == "random":
        qtype = random.choice(QUEST_TYPES[:-1])
    xp = _QXP.get(qtype, 25)

    try:
        from core.chat_engine import send_to_llm
        recent = history[-12:] if history else []
        convo = "\n".join(
            f"{m.get('role','?')}: {m.get('content','')[:220]}" for m in recent
        ) or "(no conversation yet)"
        world_line = f"World: {world.get('name','')}, {world.get('time_of_day','')}, {world.get('weather','')}." if world else ""
        char_line = f"Character: {char_name}" + (f", {character.get('profession','')}" if character else "") + "."

        prompt = (
            f"You are a quest designer for an ongoing interactive roleplay. Invent ONE {qtype} quest "
            f"that grows naturally out of what has actually happened in the conversation below -- "
            f"reference specific names, places, items, or events that were actually mentioned. Do not "
            f"invent a generic fetch quest disconnected from the story.\n\n"
            f"{char_line} {world_line}\n\nRecent conversation:\n{convo}\n\n"
            f"Respond with ONLY a single JSON object, no other text, no markdown fences:\n"
            f'{{"title": "under 12 words", "description": "2-4 sentences, specific to the story above", '
            f'"hint": "one sentence hint", "reward": "short phrase, e.g. \'40 gold\' or \'a signed letter\'"}}'
        )
        raw = send_to_llm([{"role": "system", "content": prompt}], temperature=0.85, max_tokens=300)
        data = _extract_json_object(raw)
        if not data or not data.get("title") or not data.get("description"):
            raise ValueError(f"Unparseable quest response: {raw[:200]!r}")

        title = str(data["title"])[:120]
        description = str(data["description"])[:600]
        hint = str(data.get("hint", "") or random.choice(HINTS))[:200]
        reward = f"{data.get('reward', random.choice(REWARDS))} | XP +{xp}"

        conn = get_conn()
        cur = conn.execute(
            "INSERT INTO quests (character_name,quest_type,title,description,reward,hint,progress,status,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (char_name, qtype, title, description, reward, hint, 0, "active", now_iso()),
        )
        qid = cur.lastrowid
        conn.commit()
        conn.close()
        return {"id": qid, "title": title, "type": qtype, "xp": xp, "dynamic": True}
    except Exception:
        log.info("Dynamic quest generation failed for %s; using templated fallback", char_name, exc_info=True)
        result = generate_quest(char_name, qtype=qtype)
        result["dynamic"] = False
        return result

def complete_quest(qid):
    conn=get_conn(); conn.execute("UPDATE quests SET progress=100,status='completed' WHERE id=?",(qid,)); conn.commit()
    r=conn.execute("SELECT character_name,quest_type FROM quests WHERE id=?",(qid,)).fetchone(); conn.close()
    if not r: return {}
    xp=_QXP.get(r["quest_type"],25)
    try:
        from core.levelling import award_xp_by_name; result=award_xp_by_name(r["character_name"],xp,f"Quest done")
        from core.relationship_engine import record_interaction; record_interaction(r["character_name"],"quest_complete",f"Quest #{qid}")
        # Add reward to inventory
        from core.storage import get_conn as gc
        ch_conn=gc(); ch=ch_conn.execute("SELECT id FROM characters WHERE name=?",(r["character_name"],)).fetchone()
        if ch:
            ch_conn.execute("INSERT INTO inventory (character_id,item_name,item_type,value,source,created_at) VALUES (?,?,?,?,?,?)",
                (ch["id"],f"Quest Reward ({r['quest_type']})",f"quest_{r['quest_type']}",xp,"quest",now_iso()))
        ch_conn.commit(); ch_conn.close()
        return result
    except Exception:
        log.debug("suppressed error", exc_info=True)
        return {}

def update_progress(qid, prog):
    conn=get_conn(); conn.execute("UPDATE quests SET progress=?,status=? WHERE id=?",(min(prog,100),"completed" if prog>=100 else "active",qid))
    conn.commit(); conn.close()
    if prog>=100: return complete_quest(qid)
    return {}

def get_active_quests(char_name=""):
    conn=get_conn()
    if char_name: rows=conn.execute("SELECT * FROM quests WHERE character_name=? AND status='active' ORDER BY id DESC",(char_name,)).fetchall()
    else: rows=conn.execute("SELECT * FROM quests WHERE status='active' ORDER BY id DESC").fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_all_quests(limit=100):
    conn=get_conn(); rows=conn.execute("SELECT * FROM quests ORDER BY id DESC LIMIT ?",(limit,)).fetchall(); conn.close()
    return [dict(r) for r in rows]

def abandon_quest(qid):
    conn=get_conn(); conn.execute("UPDATE quests SET status='abandoned' WHERE id=?",(qid,)); conn.commit(); conn.close()

def get_quest_history(char_name="", limit=20):
    """Completed or abandoned quests, most recent first."""
    conn=get_conn()
    if char_name:
        rows=conn.execute(
            "SELECT * FROM quests WHERE character_name=? AND status IN ('completed','abandoned') ORDER BY id DESC LIMIT ?",
            (char_name,limit)).fetchall()
    else:
        rows=conn.execute(
            "SELECT * FROM quests WHERE status IN ('completed','abandoned') ORDER BY id DESC LIMIT ?",
            (limit,)).fetchall()
    conn.close(); return [dict(r) for r in rows]
