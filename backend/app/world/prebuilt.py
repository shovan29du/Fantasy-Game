"""AiChat Pro v50 — Prebuilt World Templates"""

from core.logging_setup import get_logger

log = get_logger(__name__)
import random
from core.world_engine import create_world, generate_npc, create_faction, generate_dungeon, add_campaign_event, FACTION_ALIGNMENTS

# Each prebuilt world carries a "category" tag matching one of the nine
# Play-view starting categories (backend.app.domain.scenarios.CATEGORIES),
# so the New Game screen can offer at least one concrete scenario per
# category without inventing world-simulation content twice.
PREBUILT_WORLDS = {
    "Ninja Village":{"magic":"high","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":10,"npcs":8,"factions":4,
        "faction_names":["Hidden Leaf","Sand Village","Mist Village","Akatsuki"],
        "npc_profs":["Ninja","Sensei","ANBU Captain","Hokage","Medical Ninja","Rogue Ninja","Sage","Weapon Master"]},
    "Magic Academy":{"magic":"very_high","tech":"renaissance","setting":"fantasy","category":"fantasy","locations":8,"npcs":10,"factions":4,
        "faction_names":["House of Fire","House of Ice","House of Shadow","Staff of Elders"],
        "npc_profs":["Headmaster","Professor","Student","Librarian","Enchanter","Potions Master","Dueling Champion","Groundskeeper","Prefect","Ghost"]},
    "Pirate Seas":{"magic":"medium","tech":"age_of_sail","setting":"fantasy","category":"fantasy","locations":12,"npcs":8,"factions":5,
        "faction_names":["Straw Hat Crew","Marines","Warlords","Red Hair Pirates","World Government"],
        "npc_profs":["Captain","Navigator","Swordsman","Cook","Doctor","Shipwright","Marine Admiral","Bounty Hunter"]},
    "Cyberpunk City":{"magic":"none","tech":"futuristic","setting":"sci-fi","category":"cyberpunk","locations":10,"npcs":8,"factions":4,
        "faction_names":["MegaCorp","Street Runners","NetWatch","The Resistance"],
        "npc_profs":["Hacker","Street Samurai","Fixer","Corp Executive","Medtech","Techie","Netrunner","Nomad"]},
    "Dragon Realm":{"magic":"very_high","tech":"ancient","setting":"fantasy","category":"fantasy","locations":10,"npcs":6,"factions":3,
        "faction_names":["Fire Dragonborn","Ice Wyrmkin","Shadow Dragons"],
        "npc_profs":["Dragon Rider","Wyrmologist","Flame Priest","Scale Smith","Hoard Guardian","Dragon Tamer"]},
    "Hero Academy":{"magic":"high","tech":"modern","setting":"superhero","category":None,"locations":8,"npcs":10,"factions":3,
        "faction_names":["Hero Association","League of Villains","Underground"],
        "npc_profs":["Pro Hero","Student","Principal","Villain","Sidekick","Support Tech","Hero Agent","Informant","Vigilante","Reporter"]},
    "Medieval Kingdom":{"magic":"low","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":12,"npcs":10,"factions":5,
        "faction_names":["Royal Court","Thieves Guild","Knight Order","Church","Barbarian Clans"],
        "npc_profs":["King","Knight","Thief","Priest","Blacksmith","Bard","Peasant","Merchant","Wizard","Assassin"]},
    "Space Station":{"magic":"none","tech":"space_age","setting":"sci-fi","category":"alien_space","locations":8,"npcs":8,"factions":3,
        "faction_names":["Federation","Rebel Alliance","Traders Guild"],
        "npc_profs":["Captain","Engineer","Pilot","Scientist","Marine","Diplomat","AI Entity","Alien Ambassador"]},
    "Demon Slayer Corps":{"magic":"high","tech":"taisho_era","setting":"fantasy","category":"supernatural","locations":10,"npcs":8,"factions":3,
        "faction_names":["Demon Slayer Corps","Twelve Kizuki","Neutral Villages"],
        "npc_profs":["Hashira","Slayer","Kakushi","Swordsmith","Demon","Wisteria Host","Trainer","Crow Handler"]},
    "Post-Apocalypse":{"magic":"none","tech":"post_collapse","setting":"post-apocalyptic","category":"apocalyptic","locations":10,"npcs":8,"factions":4,
        "faction_names":["Vault Dwellers","Raiders","Brotherhood","Settlers"],
        "npc_profs":["Scavenger","Mechanic","Doctor","Warlord","Trader","Scout","Farmer","Engineer"]},
    "Zombie Outbreak":{"magic":"none","tech":"modern","setting":"post-apocalyptic","category":"zombie","locations":10,"npcs":8,"factions":3,
        "faction_names":["Quarantine Authority","Survivor Camps","The Infected"],
        "npc_profs":["Survivor","Medic","Scavenger","Soldier","Scientist","Looter","Guide","Ex-Cop"]},
    "Haunted Precinct":{"magic":"medium","tech":"modern","setting":"mystery","category":"mystery","locations":8,"npcs":8,"factions":3,
        "faction_names":["City Police","Occult Society","Crime Syndicate"],
        "npc_profs":["Detective","Medium","Coroner","Informant","Suspect","Reporter","Private Eye","Ghost"]},
    "Deep Space Frontier":{"magic":"none","tech":"futuristic","setting":"sci-fi","category":"alien_space","locations":9,"npcs":8,"factions":3,
        "faction_names":["Colonial Fleet","Xenarch Collective","Independent Traders"],
        "npc_profs":["Starship Captain","Xenobiologist","Alien Diplomat","Smuggler","Engineer","Scout","AI Core","Bounty Hunter"]},
}

def get_prebuilt_list(): return list(PREBUILT_WORLDS.keys())

def get_prebuilt_by_category(category: str):
    return [name for name, t in PREBUILT_WORLDS.items() if t.get("category") == category]

def create_prebuilt_world(name, reality_type=None):
    t=PREBUILT_WORLDS.get(name)
    if not t: return {"error":"Unknown template"}
    w=create_world(name,t.get("magic","medium"),t.get("tech","middle_age"),t.get("setting","fantasy"),t.get("locations",8),
                    reality_type=reality_type or "Prime Reality")
    wid=w["id"]
    for fn in t.get("faction_names",[]): create_faction(wid,fn,random.choice(FACTION_ALIGNMENTS))
    profs=t.get("npc_profs",[])
    for i in range(t.get("npcs",6)):
        custom={"profession":profs[i%len(profs)]} if profs else {}
        if t.get("faction_names"): custom["faction"]=random.choice(t["faction_names"])
        generate_npc(wid,custom)
    generate_dungeon(wid,levels=2,rooms_per=5); generate_dungeon(wid,levels=3,rooms_per=4)
    add_campaign_event(wid,"creation",f"Prebuilt world '{name}' created.",0)
    try:
        from core.simulation_engine import init_market; init_market(wid)
    except Exception:
        log.debug("suppressed error", exc_info=True)
        pass
    return w
