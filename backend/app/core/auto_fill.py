"""AiChat Pro — Character Auto-Fill + Picture Prompt Generation"""

from core.logging_setup import get_logger

log = get_logger(__name__)
import random, json
from core.character_data import (DND_RACES, GENDERS, BODY_TYPES, ALIGNMENTS, DND_BACKGROUNDS,
    PROFESSIONS, WEAPON_TYPES, MAGIC_TYPES, POWER_SYSTEMS, EMOTION_STYLES, TRAITS_LIST,
    QUIRKS_LIST, SKILLS_LIST, CHARACTER_TAGS, random_measurements)

def auto_fill_character(ch):
    ch["level"]=1; ch["xp"]=0
    ch.setdefault("name",f"Import_{random.randint(1000,9999)}")
    ch.setdefault("age",random.randint(18,35))
    if not ch.get("gender") or ch.get("gender") not in GENDERS: ch["gender"]=random.choice(GENDERS[:3])
    if not ch.get("race") or ch.get("race") not in DND_RACES: ch["race"]="Human"
    rd=DND_RACES.get(ch["race"],DND_RACES["Human"])
    ch.setdefault("alignment",random.choice(ALIGNMENTS))
    ch.setdefault("background",random.choice(DND_BACKGROUNDS[:-1]))
    ch.setdefault("profession",random.choice(PROFESSIONS[:-1]))
    ch.setdefault("skin",random.choice(rd.get("skin",["Fair"])))
    ch.setdefault("hair",random.choice(rd.get("hair",["Black"])))
    ch.setdefault("eyes",random.choice(rd.get("eyes",["Brown"])))
    ch.setdefault("body_type",random.choice(BODY_TYPES[:10]))
    ch.setdefault("height",rd.get("height","5'8\""))
    if not ch.get("bust_chest") or not ch.get("waist") or not ch.get("hips"):
        b,w,h=random_measurements(ch["race"],ch["gender"])
        ch.setdefault("bust_chest",b); ch.setdefault("waist",w); ch.setdefault("hips",h)
    bmap={"STR":"strength","DEX":"dexterity","INT":"intelligence","WIS":"wisdom","CON":"constitution","CHA":"charisma_stat"}
    bonuses=rd.get("stat_bonuses",{})
    for s in ["strength","dexterity","intelligence","wisdom","constitution","speed","luck","charisma_stat"]:
        if not ch.get(s) or ch.get(s,0)==0:
            base=10
            for bk,bv in bonuses.items():
                val=int(bv.replace("+",""))
                if bk=="All": base+=val
                elif bk in bmap and bmap[bk]==s: base+=val
            ch[s]=min(base+random.randint(-2,3),20)
    ch.setdefault("looks",random.randint(4,8))
    for k in ["weapon_training","magic_type","power_system","spells","traits","quirks","skills","emotion_styles","tags"]:
        _el(ch,k)
    if not ch["weapon_training"]:
        p=ch.get("profession","").lower()
        if any(w in p for w in ["soldier","gladiator","knight"]): ch["weapon_training"]=["Sword"]
        elif any(w in p for w in ["assassin","thief","ninja"]): ch["weapon_training"]=["Dagger"]
        elif any(w in p for w in ["wizard","necromancer"]): ch["weapon_training"]=["Staff"]
        elif any(w in p for w in ["ranger","hunter"]): ch["weapon_training"]=["Bow"]
        elif "monk" in p: ch["weapon_training"]=["Martial Arts"]
        else: ch["weapon_training"]=[random.choice(WEAPON_TYPES[:15])]
    if not ch["magic_type"]:
        p=ch.get("profession","").lower()
        if any(w in p for w in ["wizard","mage"]): ch["magic_type"]=random.sample(MAGIC_TYPES[:15],2)
        elif any(w in p for w in ["healer","priest"]): ch["magic_type"]=["Healing","Light"]
        elif "necromancer" in p: ch["magic_type"]=["Death","Undead","Dark"]
    if not ch["power_system"]: ch["power_system"]=["Mana"]
    if not ch["traits"]: ch["traits"]=random.sample(TRAITS_LIST[:30],2)
    if not ch["quirks"]: ch["quirks"]=[random.choice(QUIRKS_LIST[:20])]
    if not ch["skills"]: ch["skills"]=random.sample(SKILLS_LIST[:18],3)
    if not ch["emotion_styles"]: ch["emotion_styles"]=random.sample(EMOTION_STYLES[:15],2)
    if not ch["tags"]: ch["tags"]=random.sample(CHARACTER_TAGS[:50],random.randint(2,4))
    ch.setdefault("identity_stability",random.randint(40,70))
    ch.setdefault("backstory",f"A {ch['race']} {ch['profession']} with a mysterious past.")
    ch.setdefault("scenario",""); ch.setdefault("goals","")
    if not ch.get("photo_path"): ch["photo_prompt"]=gen_photo_prompt(ch)
    return ch

def gen_photo_prompt(ch):
    p=[f"Photo portrait of a {ch.get('age',25)}-year-old {ch.get('gender','').lower()} {ch.get('race','human')} person"]
    if ch.get("profession"): p.append(f"who is a {ch['profession'].lower()}")
    a=[]
    for k,l in [("skin","skin"),("hair","hair"),("eyes","eyes"),("body_type","build")]:
        if ch.get(k): a.append(f"{ch[k]} {l}")
    if a: p.append(f"with {', '.join(a)}")
    w=ch.get("weapon_training",[])
    if isinstance(w,str):
        try: w=json.loads(w)
        except Exception:
            log.debug("suppressed error", exc_info=True)
            w=[]
    if w: p.append(f"holding a {w[0].lower()}")
    e=ch.get("emotion_styles",[])
    if isinstance(e,str):
        try: e=json.loads(e)
        except Exception:
            log.debug("suppressed error", exc_info=True)
            e=[]
    if e: p.append(f"{e[0].lower()} expression")
    p.append("realistic photo, highly detailed face, dramatic lighting, full color, professional photography")
    return ", ".join(p)

def _el(ch,key):
    v=ch.get(key)
    if v is None: ch[key]=[]; return
    if isinstance(v,str):
        try: p=json.loads(v); ch[key]=p if isinstance(p,list) else []
        except Exception:
            log.debug("suppressed error", exc_info=True)
            ch[key]=[v] if v.strip() else []
