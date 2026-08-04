"""AiChat Pro v50 — Narrative Engine
Story branching state machine, character arcs."""

from core.logging_setup import get_logger

log = get_logger(__name__)
import json, random
from core.storage import get_conn, now_iso

STORY_STATES = {
    "start":{"transitions":["peace","conflict","mystery"]}, "peace":{"transitions":["trade_boom","festival","conflict","betrayal"]},
    "conflict":{"transitions":["war","diplomacy","retreat"]}, "mystery":{"transitions":["investigation","revelation","trap"]},
    "trade_boom":{"transitions":["prosperity","corruption","peace"]}, "festival":{"transitions":["peace","assassination","romance"]},
    "betrayal":{"transitions":["war","exile","revenge"]}, "war":{"transitions":["victory","defeat","ceasefire"]},
    "diplomacy":{"transitions":["peace","alliance","betrayal"]}, "retreat":{"transitions":["exile","regroup","surrender"]},
    "investigation":{"transitions":["revelation","ambush","dead_end"]}, "revelation":{"transitions":["peace","conflict","transformation"]},
    "trap":{"transitions":["escape","capture","sacrifice"]}, "prosperity":{"transitions":["peace","corruption","expansion"]},
    "corruption":{"transitions":["revolution","tyranny","reform"]}, "assassination":{"transitions":["chaos","succession","revenge"]},
    "romance":{"transitions":["peace","heartbreak","alliance"]}, "victory":{"transitions":["peace","expansion","celebration"]},
    "defeat":{"transitions":["exile","revenge","surrender"]}, "ceasefire":{"transitions":["peace","cold_war","trade_boom"]},
    "alliance":{"transitions":["peace","prosperity","war"]}, "exile":{"transitions":["return","new_beginning","revenge"]},
    "revenge":{"transitions":["victory","defeat","redemption"]}, "escape":{"transitions":["freedom","pursuit","hide"]},
    "capture":{"transitions":["escape","trial","execution"]}, "sacrifice":{"transitions":["redemption","tragedy","legend"]},
    "revolution":{"transitions":["new_order","chaos","reform"]}, "tyranny":{"transitions":["revolution","submission","exile"]},
    "reform":{"transitions":["peace","prosperity","resistance"]},
    "redemption":{"transitions":[],"ending":True}, "legend":{"transitions":[],"ending":True},
    "new_order":{"transitions":[],"ending":True}, "tragedy":{"transitions":[],"ending":True},
    "freedom":{"transitions":[],"ending":True}, "submission":{"transitions":[],"ending":True},
}

ARC_TYPES = {
    "corruption":{"stages":["innocent","tempted","compromised","fallen","dark_lord"],"stat":"wisdom","dir":-1},
    "redemption":{"stages":["fallen","doubt","seeking","tested","redeemed"],"stat":"wisdom","dir":1},
    "romance":{"stages":["stranger","curious","attracted","devoted","soulbound"],"stat":"charisma_stat","dir":1},
    "betrayal":{"stages":["trusted","suspicious","deceived","broken","vengeful"],"stat":"luck","dir":-1},
    "heroism":{"stages":["ordinary","called","tested","triumphant","legendary"],"stat":"strength","dir":1},
    "madness":{"stages":["sane","stressed","cracking","unhinged","lost"],"stat":"wisdom","dir":-1},
    "ascension":{"stages":["mortal","awakened","channeling","transcending","divine"],"stat":"intelligence","dir":1},
}

def get_story_state(wid):
    conn=get_conn(); r=conn.execute("SELECT value FROM settings WHERE key=?",(f"story_state_{wid}",)).fetchone(); conn.close()
    return r["value"] if r else "start"

def set_story_state(wid, state):
    conn=get_conn(); conn.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)",(f"story_state_{wid}",state)); conn.commit(); conn.close()

def advance_story(wid, choice=None):
    cur=get_story_state(wid); info=STORY_STATES.get(cur,{"transitions":["start"]})
    if info.get("ending"): return {"state":cur,"ending":True}
    ts=info.get("transitions",["start"])
    if not ts: return {"state":cur,"ending":True}
    ns=choice if choice and choice in ts else random.choice(ts)
    set_story_state(wid,ns)
    conn=get_conn(); tick_r=conn.execute("SELECT world_tick FROM worlds WHERE id=?",(wid,)).fetchone()
    tick=tick_r["world_tick"] if tick_r else 0
    conn.execute("INSERT INTO campaign_events (world_id,event_type,description,tick,created_at) VALUES (?,?,?,?,?)",(wid,"narrative",f"Story: {cur} → {ns}",tick,now_iso()))
    conn.commit(); conn.close()
    return {"previous":cur,"state":ns,"options":STORY_STATES.get(ns,{}).get("transitions",[]),"ending":STORY_STATES.get(ns,{}).get("ending",False)}

def get_character_arc(name):
    conn=get_conn(); r=conn.execute("SELECT value FROM settings WHERE key=?",(f"arc_{name}",)).fetchone(); conn.close()
    if r:
        try: return json.loads(r["value"])
        except Exception:
            log.debug("suppressed error", exc_info=True)
            pass
    return None

def start_character_arc(name, arc_type):
    arc=ARC_TYPES.get(arc_type)
    if not arc: return {"error":"Unknown arc"}
    data={"type":arc_type,"stage":0,"stages":arc["stages"],"stat":arc["stat"],"dir":arc["dir"]}
    conn=get_conn(); conn.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)",(f"arc_{name}",json.dumps(data))); conn.commit(); conn.close()
    return data

def advance_character_arc(name):
    arc=get_character_arc(name)
    if not arc: return {"error":"No active arc"}
    if arc["stage"]>=len(arc["stages"])-1: return {"stage":arc["stages"][-1],"complete":True}
    arc["stage"]+=1
    conn=get_conn(); conn.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)",(f"arc_{name}",json.dumps(arc))); conn.commit(); conn.close()
    return {"stage_name":arc["stages"][arc["stage"]],"stage_index":arc["stage"],"total":len(arc["stages"]),"complete":arc["stage"]>=len(arc["stages"])-1}

def get_narrative_prompt(wid, char_name=""):
    state=get_story_state(wid); parts=[f"[Narrative: {state}]"]
    info=STORY_STATES.get(state,{})
    if info.get("transitions"): parts.append(f"[Paths: {', '.join(info['transitions'][:4])}]")
    if char_name:
        arc=get_character_arc(char_name)
        if arc:
            sn=arc["stages"][arc["stage"]] if arc["stage"]<len(arc["stages"]) else "complete"
            parts.append(f"[Arc: {arc['type']}, stage: {sn}]")
    return " ".join(parts)
