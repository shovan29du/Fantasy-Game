"""AiChat Pro — World Engine (v7) — All 22 systems integrated
World time, NPC routines, weather, resources, population, law/crime,
diplomacy, territory, factions, economy, combat, campaign, random events."""

from core.logging_setup import get_logger

log = get_logger(__name__)
import json, random
from datetime import datetime
from typing import List, Dict, Optional
from core.storage import get_conn, now_iso
from core.db_migration import migrate_db

TERRAINS=["Forest","Desert","Mountain","Ocean","Swamp","Volcano","Plains","City","Ruins","Space","Underground","Tundra","Jungle","Savanna","Canyon"]
MAGIC_LEVELS=["none","low","medium","high","legendary"]
TECH_LEVELS=["stone_age","bronze_age","iron_age","middle_age","renaissance","steam","modern","sci_fi","custom"]
SPACE_ALIGNMENTS=["fantasy","earth","galactic","multiverse","pocket_dimension"]
FACTION_ALIGNMENTS=["Lawful Good","Neutral Good","Chaotic Good","Lawful Neutral","True Neutral","Chaotic Neutral","Lawful Evil","Neutral Evil","Chaotic Evil"]
NPC_PROFESSIONS=["Blacksmith","Merchant","Guard","Healer","Scholar","Innkeeper","Farmer","Hunter","Thief","Wizard","Priest","Bard","Noble","Soldier","Assassin","Doctor","Lawyer","Chef","Engineer","Mafia Boss"]
NPC_PERSONALITIES=["Friendly","Suspicious","Greedy","Wise","Cowardly","Brave","Mysterious","Jolly","Stern","Cunning"]
DUNGEON_TYPES=["random","boss","puzzle","trap","multi_level","treasure"]
ROOM_TYPES=["entrance","corridor","trap_room","monster_lair","treasure_room","boss_chamber","secret_passage","checkpoint","puzzle_room","shrine"]
WEATHERS=["clear","cloudy","rain","storm","snow","fog","heatwave","blizzard","sandstorm","magical_aurora"]
TIMES=["dawn","morning","midday","afternoon","dusk","evening","night","midnight"]
RESOURCES=["wood","stone","iron","gold_ore","food","water","mana_crystals","herbs","leather","gems"]
RANDOM_EVENTS=["Merchant caravan arrives","Bandit raid on settlement","Natural disaster","Festival celebration","Disease outbreak","Monster sighting","Political assassination","Trade route discovered","Ancient ruins found","Celestial event","Famine","Gold rush","War declaration","Peace treaty","Religious miracle","Dragon sighting","Earthquake","Flood","Wildfire","Mysterious fog"]
LAWS=["No murder","No theft","No trespassing","Curfew after dark","No magic in public","Weapons license required","Trade tax 10%","No slavery","Religious freedom","Free speech"]
_NA=["Ael","Bran","Cal","Dor","Eld","Fen","Gor","Har","Ith","Jar","Kal","Lor","Mor","Nar","Oth","Par","Quen","Rath","Sal","Tor","Ul","Val","Wyn","Xar","Zeph"]
_NB=["andir","eth","ius","on","ar","iel","wyn","ax","oth","ren","is","or","un","il","ek"]
def _rn(): return random.choice(_NA)+random.choice(_NB)

# ── WORLD CRUD ──
def create_world(name, magic="medium", tech="middle_age", space="fantasy", num_locs=8):
    migrate_db()
    locs=[]
    for i in range(num_locs):
        t=random.choice(TERRAINS)
        locs.append({"name":f"{t} of {_rn()}","terrain":t,"x":random.randint(0,100),"y":random.randint(0,100),
            "description":f"A {t.lower()} region with unique features.","population":random.randint(50,500),
            "resources":{random.choice(RESOURCES):random.randint(50,200) for _ in range(2)}})
    wd={"name":name,"magic_level":magic,"tech_level":tech,"space_alignment":space,"locations":locs}
    conn=get_conn()
    cur=conn.execute("INSERT INTO worlds (name,magic_level,tech_level,space_alignment,world_json,created_at) VALUES (?,?,?,?,?,?)",
        (name,magic,tech,space,json.dumps(wd),now_iso()))
    wid=cur.lastrowid
    for loc in locs:
        conn.execute("INSERT INTO world_locations (world_id,name,loc_type,terrain,description,x,y,resources_json,population) VALUES (?,?,?,?,?,?,?,?,?)",
            (wid,loc["name"],"region",loc["terrain"],loc["description"],loc["x"],loc["y"],json.dumps(loc.get("resources",{})),loc.get("population",100)))
    # Generate default laws
    for law in random.sample(LAWS,min(5,len(LAWS))):
        conn.execute("INSERT INTO world_laws (world_id,law_name,description,penalty,active) VALUES (?,?,?,?,?)",
            (wid,law,f"Standard law: {law}","Fine or imprisonment",1))
    # Generate initial resources
    for loc in locs:
        for res,qty in loc.get("resources",{}).items():
            conn.execute("INSERT INTO world_resources (world_id,resource_type,quantity,production_rate) VALUES (?,?,?,?)",
                (wid,res,qty,random.randint(1,10)))
    conn.commit(); conn.close()
    wd["id"]=wid; return wd

def get_world(wid):
    migrate_db()
    conn=get_conn(); row=conn.execute("SELECT * FROM worlds WHERE id=?",(wid,)).fetchone(); conn.close()
    if not row: return None
    d=dict(row)
    try: d["world_json"]=json.loads(d["world_json"])
    except Exception:
        log.debug("suppressed error", exc_info=True)
        d["world_json"]={}
    return d

def list_worlds():
    migrate_db()
    conn=get_conn(); rows=conn.execute("SELECT id,name,magic_level,tech_level,world_tick,weather,time_of_day,population,created_at FROM worlds ORDER BY id DESC").fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_locations(wid):
    conn=get_conn(); rows=conn.execute("SELECT * FROM world_locations WHERE world_id=?",(wid,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

# ── WORLD TICK (time scheduler) ──
def advance_world_tick(wid):
    conn=get_conn()
    w=conn.execute("SELECT world_tick,population,treasury,crime_level FROM worlds WHERE id=?",(wid,)).fetchone()
    if not w: conn.close(); return {}
    tick=w["world_tick"]+1
    time_idx=tick%len(TIMES)
    new_time=TIMES[time_idx]
    # Weather change (20% chance)
    weather=random.choice(WEATHERS) if random.random()<0.2 else "clear"
    temp=random.choice(["freezing","cold","mild","warm","hot"])
    # Population change
    pop=max(0,w["population"]+random.randint(-5,10))
    # Treasury from taxes
    treasury=w["treasury"]+pop//10
    # Crime fluctuation
    crime=max(0,min(100,w["crime_level"]+random.randint(-3,3)))
    conn.execute("UPDATE worlds SET world_tick=?,time_of_day=?,weather=?,temperature=?,population=?,treasury=?,crime_level=? WHERE id=?",
        (tick,new_time,weather,temp,pop,treasury,crime,wid))
    # Resource production
    resources=conn.execute("SELECT id,quantity,production_rate FROM world_resources WHERE world_id=?",(wid,)).fetchall()
    for r in resources:
        conn.execute("UPDATE world_resources SET quantity=quantity+? WHERE id=?",(r["production_rate"],r["id"]))
    # Log weather
    conn.execute("INSERT INTO world_weather_log (world_id,tick,weather,temperature,created_at) VALUES (?,?,?,?,?)",
        (wid,tick,weather,temp,now_iso()))
    # Random event (10% chance)
    event=None
    if random.random()<0.1:
        event=random.choice(RANDOM_EVENTS)
        impact={"population":random.randint(-20,20),"treasury":random.randint(-100,100),"crime":random.randint(-5,5)}
        conn.execute("INSERT INTO random_events (world_id,event_text,impact_json,tick,created_at) VALUES (?,?,?,?,?)",
            (wid,event,json.dumps(impact),tick,now_iso()))
        conn.execute("INSERT INTO campaign_events (world_id,event_type,description,tick,created_at) VALUES (?,?,?,?,?)",
            (wid,"random_event",event,tick,now_iso()))
    # NPC routine update
    npcs=conn.execute("SELECT id,schedule_json FROM npcs WHERE world_id=?",(wid,)).fetchall()
    for npc in npcs:
        try:
            sched=json.loads(npc["schedule_json"] or "{}")
            activity=sched.get(new_time,"idle")
        except Exception:
            log.debug("suppressed error", exc_info=True)
            activity="idle"
        mood=random.choice(["happy","neutral","busy","tired","alert"])
        conn.execute("UPDATE npcs SET mood=? WHERE id=?",(mood,npc["id"]))
    conn.commit(); conn.close()
    return {"tick":tick,"time":new_time,"weather":weather,"temp":temp,"pop":pop,"treasury":treasury,"crime":crime,"event":event}

# ── NPC ──
def generate_npc(wid=None, custom=None):
    npc=custom or {}
    npc.setdefault("name",_rn()); npc.setdefault("age",random.randint(16,80))
    npc.setdefault("profession",random.choice(NPC_PROFESSIONS))
    npc.setdefault("personality",random.choice(NPC_PERSONALITIES))
    npc.setdefault("skills",random.choice(["Combat","Magic","Crafting","Social","Survival"]))
    npc.setdefault("alignment",random.choice(FACTION_ALIGNMENTS)); npc.setdefault("faction","")
    # Generate daily schedule
    schedule={t:random.choice(["sleeping","working","eating","training","socializing","patrolling","trading","resting"]) for t in TIMES}
    schedule["dawn"]="waking up"; schedule["night"]="sleeping"; schedule["midnight"]="sleeping"
    conn=get_conn()
    cur=conn.execute("INSERT INTO npcs (world_id,name,age,profession,personality,skills,alignment,faction,schedule_json,details_json,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (wid,npc["name"],npc["age"],npc["profession"],npc["personality"],npc["skills"],npc["alignment"],npc.get("faction",""),json.dumps(schedule),json.dumps(npc),now_iso()))
    npc["id"]=cur.lastrowid
    # Add schedule entries
    for time_slot,activity in schedule.items():
        conn.execute("INSERT INTO npc_schedules (npc_id,world_id,time_slot,activity) VALUES (?,?,?,?)",(npc["id"],wid,time_slot,activity))
    conn.commit(); conn.close(); return npc

def list_npcs(wid=None):
    conn=get_conn()
    if wid: rows=conn.execute("SELECT * FROM npcs WHERE world_id=? ORDER BY id",(wid,)).fetchall()
    else: rows=conn.execute("SELECT * FROM npcs ORDER BY id DESC LIMIT 100").fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_npc_schedule(npc_id):
    conn=get_conn(); rows=conn.execute("SELECT * FROM npc_schedules WHERE npc_id=? ORDER BY id",(npc_id,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

# ── FACTIONS ──
def create_faction(wid, name, alignment="True Neutral", leader="", territory=""):
    conn=get_conn()
    cur=conn.execute("INSERT INTO factions (world_id,name,alignment,reputation,leader,territory,created_at) VALUES (?,?,?,?,?,?,?)",
        (wid,name,alignment,50,leader,territory,now_iso()))
    fid=cur.lastrowid; conn.commit(); conn.close()
    return {"id":fid,"name":name,"alignment":alignment}

def list_factions(wid):
    conn=get_conn(); rows=conn.execute("SELECT * FROM factions WHERE world_id=?",(wid,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

# ── DIPLOMACY ──
def set_diplomacy(wid, faction_a, faction_b, relation="neutral", trade=False, treaty=""):
    conn=get_conn()
    conn.execute("INSERT OR REPLACE INTO diplomacy (world_id,faction_a,faction_b,relation,trade_active,treaty,created_at) VALUES (?,?,?,?,?,?,?)",
        (wid,faction_a,faction_b,relation,1 if trade else 0,treaty,now_iso()))
    conn.commit(); conn.close()

def get_diplomacy(wid):
    conn=get_conn(); rows=conn.execute("SELECT * FROM diplomacy WHERE world_id=?",(wid,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

# ── DUNGEONS ──
def generate_dungeon(wid=None, name="", dtype="random", levels=1, rooms_per=5):
    if not name: name=f"Dungeon of {_rn()}"
    if dtype=="random": dtype=random.choice(DUNGEON_TYPES[1:])
    rooms=[]
    for lvl in range(1,levels+1):
        for r in range(rooms_per):
            rt=random.choice(ROOM_TYPES)
            rooms.append({"level":lvl,"room_number":r+1,"type":rt,"description":f"A {rt.replace('_',' ')} on level {lvl}.",
                "has_monster":rt in ("monster_lair","boss_chamber"),"has_treasure":rt in ("treasure_room","boss_chamber"),"has_trap":rt=="trap_room"})
    conn=get_conn()
    cur=conn.execute("INSERT INTO dungeons (world_id,name,dungeon_type,levels,rooms_json,created_at) VALUES (?,?,?,?,?,?)",
        (wid,name,dtype,levels,json.dumps(rooms),now_iso()))
    did=cur.lastrowid; conn.commit(); conn.close()
    return {"id":did,"name":name,"type":dtype,"levels":levels,"rooms":rooms}

def list_dungeons(wid=None):
    conn=get_conn()
    if wid: rows=conn.execute("SELECT id,name,dungeon_type,levels,created_at FROM dungeons WHERE world_id=?",(wid,)).fetchall()
    else: rows=conn.execute("SELECT id,name,dungeon_type,levels,created_at FROM dungeons ORDER BY id DESC LIMIT 50").fetchall()
    conn.close(); return [dict(r) for r in rows]

# ── COMBAT ──
def simulate_combat(attacker, defender):
    ap=attacker.get("strength",10)+random.randint(1,20); dp=defender.get("constitution",10)+random.randint(1,20)
    crit=random.random()<0.1
    if crit: ap*=2
    dmg=max(0,ap-dp//2)
    result={"attacker":attacker.get("name","Attacker"),"defender":defender.get("name","Defender"),
        "attack_roll":ap,"defense_roll":dp,"critical":crit,"damage":dmg,
        "winner":attacker.get("name") if dmg>0 else defender.get("name")}
    conn=get_conn()
    conn.execute("INSERT INTO combat_logs (attacker,defender,result_json,created_at) VALUES (?,?,?,?)",
        (result["attacker"],result["defender"],json.dumps(result),now_iso()))
    conn.commit(); conn.close(); return result

# ── ECONOMY ──
def ensure_economy(cid):
    conn=get_conn()
    if not conn.execute("SELECT 1 FROM economy WHERE character_id=?",(cid,)).fetchone():
        conn.execute("INSERT INTO economy (character_id) VALUES (?)",(cid,))
        conn.commit()
    conn.close()

def earn_currency(cid, amount, currency="gold", reason=""):
    ensure_economy(cid); conn=get_conn()
    conn.execute(f"UPDATE economy SET {currency}={currency}+? WHERE character_id=?",(amount,cid))
    conn.execute("INSERT INTO transactions (character_id,tx_type,amount,currency,reason,created_at) VALUES (?,?,?,?,?,?)",(cid,"income",amount,currency,reason,now_iso()))
    conn.commit(); conn.close()

def spend_currency(cid, amount, currency="gold", reason=""):
    ensure_economy(cid); conn=get_conn()
    row=conn.execute(f"SELECT {currency} FROM economy WHERE character_id=?",(cid,)).fetchone()
    if not row or row[0]<amount: conn.close(); return False
    conn.execute(f"UPDATE economy SET {currency}={currency}-? WHERE character_id=?",(amount,cid))
    conn.execute("INSERT INTO transactions (character_id,tx_type,amount,currency,reason,created_at) VALUES (?,?,?,?,?,?)",(cid,"expense",amount,currency,reason,now_iso()))
    conn.commit(); conn.close(); return True

def get_economy(cid):
    ensure_economy(cid); conn=get_conn()
    row=conn.execute("SELECT * FROM economy WHERE character_id=?",(cid,)).fetchone()
    conn.close(); return dict(row) if row else {}

# ── CAMPAIGN TIMELINE ──
def add_campaign_event(wid, etype, desc, tick=0):
    conn=get_conn()
    conn.execute("INSERT INTO campaign_events (world_id,event_type,description,tick,created_at) VALUES (?,?,?,?,?)",(wid,etype,desc,tick,now_iso()))
    conn.commit(); conn.close()

def get_timeline(wid):
    conn=get_conn(); rows=conn.execute("SELECT * FROM campaign_events WHERE world_id=? ORDER BY tick,id",(wid,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

# ── RESOURCES ──
def get_resources(wid):
    conn=get_conn(); rows=conn.execute("SELECT * FROM world_resources WHERE world_id=?",(wid,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

# ── LAWS ──
def get_laws(wid):
    conn=get_conn(); rows=conn.execute("SELECT * FROM world_laws WHERE world_id=?",(wid,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

def add_law(wid, name, desc="", penalty="Fine"):
    conn=get_conn(); conn.execute("INSERT INTO world_laws (world_id,law_name,description,penalty) VALUES (?,?,?,?)",(wid,name,desc,penalty))
    conn.commit(); conn.close()

# ── RANDOM EVENTS ──
def get_random_events(wid, limit=20):
    conn=get_conn(); rows=conn.execute("SELECT * FROM random_events WHERE world_id=? ORDER BY id DESC LIMIT ?",(wid,limit)).fetchall()
    conn.close(); return [dict(r) for r in rows]

# ── WEATHER LOG ──
def get_weather_log(wid, limit=20):
    conn=get_conn(); rows=conn.execute("SELECT * FROM world_weather_log WHERE world_id=? ORDER BY id DESC LIMIT ?",(wid,limit)).fetchall()
    conn.close(); return [dict(r) for r in rows]

# ── CAMPAIGN SAVE/LOAD ──
def save_campaign(wid, save_name):
    w=get_world(wid)
    if not w: return False
    conn=get_conn()
    locs=[dict(r) for r in conn.execute("SELECT * FROM world_locations WHERE world_id=?",(wid,)).fetchall()]
    npcs=[dict(r) for r in conn.execute("SELECT * FROM npcs WHERE world_id=?",(wid,)).fetchall()]
    factions=[dict(r) for r in conn.execute("SELECT * FROM factions WHERE world_id=?",(wid,)).fetchall()]
    events=[dict(r) for r in conn.execute("SELECT * FROM campaign_events WHERE world_id=?",(wid,)).fetchall()]
    save_data={"world":w,"locations":locs,"npcs":npcs,"factions":factions,"events":events}
    conn.execute("INSERT INTO campaign_saves (world_id,save_name,save_json,created_at) VALUES (?,?,?,?)",
        (wid,save_name,json.dumps(save_data,default=str),now_iso()))
    conn.commit(); conn.close(); return True

def list_campaign_saves(wid):
    conn=get_conn(); rows=conn.execute("SELECT id,save_name,created_at FROM campaign_saves WHERE world_id=? ORDER BY id DESC",(wid,)).fetchall()
    conn.close(); return [dict(r) for r in rows]
