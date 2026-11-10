"""Organizations system: guilds, families, businesses, academies, orders."""
from __future__ import annotations
import json, re
from core.storage import get_conn, now_iso
from core.logging_setup import get_logger
log = get_logger(__name__)

ORG_TYPES = ["guild","family","noble_house","business","academy","order",
             "council","brotherhood","cult","military","criminal"]

TEMPLATE_ORGS = [
    {"name":"Thieves' Guild","org_type":"guild","focus":"stealth","primary_attr":"dexterity",
     "description":"A clandestine network of thieves, spies, and information brokers operating in the shadows of the city.",
     "ranks":["Rat","Member","Agent","Handler","Shadow","Guildmaster"],
     "join_req":{"level":2},"treasury":5000,
     "benefits":{"0":"Fencing discount 20%","1":"+1 DEX, access to guild safehouses","2":"Poison recipes, +1 lockpicking","3":"Spy network contact, +2 DEX","4":"Shadow network: gather info on anyone","5":"Command thieves' operations, 10% cut of guild income"}},
    {"name":"Mages' Academy","org_type":"academy","focus":"magic","primary_attr":"intelligence",
     "description":"A prestigious institution of magical learning where arcane arts are studied and mastered.",
     "ranks":["Apprentice","Student","Adept","Scholar","Magister","Archmage"],
     "join_req":{"level":1,"attr":{"intelligence":12}},"treasury":8000,
     "benefits":{"0":"Library access (+1 research)","1":"+1 INT, free spell slot per day","2":"Mentor NPC, learn extra spell","3":"Lab access, craft potions/scrolls","4":"+2 INT, restricted tomes","5":"Title of Archmage, cast one epic spell per month"}},
    {"name":"Fighters' Hall","org_type":"guild","focus":"combat","primary_attr":"strength",
     "description":"A brotherhood of warriors and mercenaries who train together and take contracts.",
     "ranks":["Recruit","Soldier","Veteran","Sergeant","Captain","Warlord"],
     "join_req":{"level":1,"attr":{"strength":12}},"treasury":3000,
     "benefits":{"0":"Training grounds access","1":"+1 STR, free weapon repair","2":"Combat mentor, learn a combat feat","3":"+1 to all attack rolls on contracts","4":"+2 STR, lead a unit of 10 fighters","5":"Command an army, legendary combat title"}},
    {"name":"Merchants' Council","org_type":"council","focus":"economy","primary_attr":"charisma_stat",
     "description":"A powerful council of traders controlling commerce across the region.",
     "ranks":["Peddler","Trader","Merchant","Magnate","Director","Guild Lord"],
     "join_req":{"level":1,"gold":100},"treasury":20000,
     "benefits":{"0":"10% trade discount","1":"Shop access, +1 CHA","2":"Trade routes, 20% buy/sell bonus","3":"Political connections, Noble access","4":"+2 CHA, run your own business","5":"Control regional market prices"}},
    {"name":"Temple of Light","org_type":"order","focus":"divine","primary_attr":"wisdom",
     "description":"A religious order devoted to healing, justice, and the protection of the innocent.",
     "ranks":["Acolyte","Initiate","Priest","Elder","Hierophant","High Priest"],
     "join_req":{"level":1},"treasury":4000,
     "benefits":{"0":"Free healing potions (1/week)","1":"+1 WIS, sanctuary in temple","2":"Divine insight, adv. on WIS checks","3":"+1 to all saving throws, holy weapon","4":"+2 WIS, divine magic access","5":"Commune with gods (1/month)"}},
    {"name":"Scout Rangers","org_type":"military","focus":"exploration","primary_attr":"dexterity",
     "description":"Elite scouts and rangers who patrol the wilderness and map unknown territory.",
     "ranks":["Scout","Ranger","Tracker","Pathfinder","Captain","Master Ranger"],
     "join_req":{"level":2},"treasury":2000,
     "benefits":{"0":"Wilderness survival advantage","1":"+1 DEX, ranger's pack","2":"Animal companion (1 beast)","3":"Territory maps, +1 tracking","4":"+2 DEX, command a ranger unit","5":"Lead expeditions, legendary ranger title"}},
    {"name":"Alchemists' Brotherhood","org_type":"brotherhood","focus":"crafting","primary_attr":"intelligence",
     "description":"A secretive guild of alchemists who brew rare potions and unlock mysteries of transformation.",
     "ranks":["Novice","Brewer","Alchemist","Transmuter","Master","Grand Master"],
     "join_req":{"level":2,"attr":{"intelligence":12}},"treasury":6000,
     "benefits":{"0":"Recipe access, 10% potion discount","1":"+1 INT, craft basic potions","2":"Craft uncommon potions, explosion immunity","3":"+1 craft checks, rare recipes","4":"+2 INT, craft rare potions","5":"Craft legendary potions, transmutation mastery"}},
    {"name":"Shadow Court","org_type":"criminal","focus":"crime","primary_attr":"charisma_stat",
     "description":"A powerful criminal organization controlling the underworld.",
     "ranks":["Errand Boy","Foot Soldier","Enforcer","Lieutenant","Underboss","Crime Lord"],
     "join_req":{"level":3},"treasury":15000,
     "benefits":{"0":"Criminal contacts, bounty immunity (local)","1":"+1 CHA, 50% fencing value","2":"Hired muscle (2 thugs), mark intelligence","3":"Blackmail resources, bribe officials","4":"+2 CHA, control a district","5":"Command criminal empire"}},
    {"name":"Royal House of Stars","org_type":"noble_house","focus":"politics","primary_attr":"charisma_stat",
     "description":"An ancient noble family with deep political connections and vast ancestral wealth.",
     "ranks":["Ward","Squire","Knight","Baron","Lord","Patriarch"],
     "join_req":{"level":4},"treasury":50000,
     "benefits":{"0":"Minor noble title, courtly access","1":"+1 CHA, noble wardrobe","2":"Political favor, +1 to social checks","3":"Land grant, soldiers (10)","4":"+2 CHA, seat on council","5":"Rule a province, royal bloodline recognized"}},
    {"name":"Artificers' Union","org_type":"guild","focus":"technology","primary_attr":"intelligence",
     "description":"A union of engineers, tinkerers, and inventors pushing the boundaries of technology.",
     "ranks":["Apprentice","Journeyman","Craftsman","Engineer","Master","Chief Engineer"],
     "join_req":{"level":2,"attr":{"intelligence":13}},"treasury":7000,
     "benefits":{"0":"Workshop access, 10% parts discount","1":"+1 INT, craft gadgets","2":"Blueprints for mechanical constructs","3":"+1 to all INT craft checks","4":"+2 INT, build siege engines","5":"Create legendary artifacts (1/month)"}},
]

def get_orgs_for_world(world_id: int) -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM organizations WHERE world_id=? ORDER BY name", (world_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_template_orgs() -> list[dict]:
    return TEMPLATE_ORGS

def get_character_memberships(char_id: int) -> list[dict]:
    conn = get_conn()
    rows = conn.execute("""
        SELECT o.*, om.rank as member_rank, om.contributions, om.joined_at as member_since
        FROM organizations o
        JOIN org_members om ON o.id = om.org_id
        WHERE om.character_id=?
        ORDER BY om.joined_at
    """, (char_id,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["ranks"] = json.loads(d.get("ranks_json") or "[]")
        d["benefits"] = json.loads(d.get("benefits_json") or "{}")
        result.append(d)
    return result

def join_org(org_id: int, char_id: int) -> dict:
    conn = get_conn()
    try:
        ex = conn.execute("SELECT id FROM org_members WHERE org_id=? AND character_id=?", (org_id, char_id)).fetchone()
        if ex:
            return {"ok": False, "error": "Already a member"}
        conn.execute("INSERT INTO org_members (org_id,character_id,rank,joined_at,contributions) VALUES (?,?,0,?,0)",
                     (org_id, char_id, now_iso()))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()

def rank_up_member(org_id: int, char_id: int) -> dict:
    conn = get_conn()
    try:
        mem = conn.execute("SELECT rank FROM org_members WHERE org_id=? AND character_id=?", (org_id, char_id)).fetchone()
        if not mem:
            return {"ok": False, "error": "Not a member"}
        org = conn.execute("SELECT ranks_json FROM organizations WHERE id=?", (org_id,)).fetchone()
        if not org:
            return {"ok": False, "error": "Organization not found"}
        ranks = json.loads(org["ranks_json"] or "[]")
        cur_rank = mem["rank"]
        if cur_rank >= len(ranks) - 1:
            return {"ok": False, "error": "Already at max rank"}
        new_rank = cur_rank + 1
        conn.execute("UPDATE org_members SET rank=? WHERE org_id=? AND character_id=?", (new_rank, org_id, char_id))
        conn.commit()
        return {"ok": True, "new_rank": new_rank, "rank_name": ranks[new_rank] if new_rank < len(ranks) else "Max"}
    finally:
        conn.close()

def leave_org(org_id: int, char_id: int) -> dict:
    conn = get_conn()
    conn.execute("DELETE FROM org_members WHERE org_id=? AND character_id=?", (org_id, char_id))
    conn.commit(); conn.close()
    return {"ok": True}

def seed_world_orgs(world_id: int) -> int:
    conn = get_conn()
    existing = conn.execute("SELECT COUNT(*) FROM organizations WHERE world_id=?", (world_id,)).fetchone()[0]
    conn.close()
    if existing > 0:
        return existing
    count = 0
    for org in TEMPLATE_ORGS:
        conn = get_conn()
        conn.execute("""INSERT INTO organizations
            (world_id,name,org_type,focus,primary_attr,description,ranks_json,benefits_json,join_req_json,treasury,reputation,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,50,?)""",
            (world_id, org["name"], org["org_type"], org["focus"], org["primary_attr"],
             org["description"], json.dumps(org["ranks"]), json.dumps(org["benefits"]),
             json.dumps(org.get("join_req",{})), org.get("treasury",0), now_iso()))
        conn.commit(); conn.close()
        count += 1
    return count

def generate_story_org(world_id: int, history: list | None = None, world_name: str = "") -> dict:
    """Generate a story-synced organization via LLM."""
    try:
        from core.chat_engine import send_to_llm
        recent = (history or [])[-10:]
        convo = "\n".join(f"{m.get('role','?')}: {m.get('content','')[:200]}" for m in recent) or "(no context)"
        prompt = (
            f"Based on this RPG story, invent ONE unique organization (guild, family, business, "
            f"academy, order, etc.) that would naturally appear in the narrative. "
            f"World: {world_name or 'Fantasy world'}\n\nRecent story:\n{convo}\n\n"
            "Respond ONLY with a JSON object (no markdown backticks):\n"
            '{"name":"org name","org_type":"guild","focus":"one word","description":"2-3 sentences",'
            '"ranks":["Rank1","Rank2","Rank3","Rank4","Rank5","Rank6"],'
            '"story_origin":"one sentence about why this org exists"}'
        )
        raw = send_to_llm([{"role":"system","content":prompt}], temperature=0.8, max_tokens=400)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError("No JSON in response")
        data = json.loads(match.group(0))
        conn = get_conn()
        cur = conn.execute("""INSERT INTO organizations
            (world_id,name,org_type,focus,primary_attr,description,ranks_json,benefits_json,
             join_req_json,story_origin,reputation,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,50,?)""",
            (world_id, data["name"], data.get("org_type","guild"), data.get("focus","general"),
             "", data.get("description",""), json.dumps(data.get("ranks",["Member","Elder"])),
             "{}", "{}", data.get("story_origin",""), now_iso()))
        org_id = cur.lastrowid; conn.commit(); conn.close()
        return {"ok":True,"id":org_id,"name":data["name"],"dynamic":True,
                "org_type":data.get("org_type","guild"),"description":data.get("description","")}
    except Exception as exc:
        log.info("Dynamic org gen failed: %s", exc)
        return {"ok":False,"error":str(exc)}
