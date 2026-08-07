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
    "The Wrongly Accused":{"magic":"high","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":8,"npcs":8,"factions":3,
        "faction_names":["The Sect","Prison Wardens","The True Culprit's Circle"],
        "npc_profs":["Sect Master","Loyal Spouse","Real Culprit","Prison Warden","Childhood Friend","Investigator","Rival Disciple","Sect Elder's Ghost"]},
    "The Traitor's Escape":{"magic":"medium","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":9,"npcs":8,"factions":3,
        "faction_names":["Royal Guard","Rebel Sympathizers","Exiled Nobles"],
        "npc_profs":["Princess","Captain of the Guard","Loyalist Spy","Mercenary Ally","Village Healer","Court Informant","Bounty Hunter","Old Mentor"]},
    "The Suitor's Tournament":{"magic":"medium","tech":"renaissance","setting":"fantasy","category":"fantasy","locations":6,"npcs":8,"factions":3,
        "faction_names":["Competing Houses","Royal Court","Foreign Delegation"],
        "npc_profs":["Princess","King","Rival Suitor","Tournament Herald","Court Matchmaker","Bodyguard","Visiting Prince","Court Jester"]},
    "Blade for Hire":{"magic":"medium","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":9,"npcs":8,"factions":3,
        "faction_names":["Mercenary Guild","Deposed Royalty","Usurper's Court"],
        "npc_profs":["Princess","Usurper King","Mercenary Captain","Old Retainer","Rival Mercenary","Spy","Exiled Advisor","Border Guard"]},
    "The Prince's Champion":{"magic":"medium","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":8,"npcs":8,"factions":3,
        "faction_names":["Royal Household","Knight's Order","Invading Force"],
        "npc_profs":["Prince","Princess","Childhood Friend Turned Warrior","Court Advisor","Enemy Commander","Old Mentor","Royal Guard Captain","Court Healer"]},
    "Fifteen Years a Prisoner":{"magic":"medium","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":7,"npcs":6,"factions":3,
        "faction_names":["The Warden's Order","Old Kingdom Loyalists","The Rebellion"],
        "npc_profs":["The Prisoner","The Warden","Old Ally","Rebel Leader","Former Confidant","Prison Guard"]},
    "Human and the Elven Queen":{"magic":"very_high","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":9,"npcs":8,"factions":3,
        "faction_names":["Human Kingdom","Elven Court","Border Clans"],
        "npc_profs":["Elven Queen","Human Envoy","Elven Advisor","Human General","Half-Elf Guide","Ancient Spirit","Border Scout","Elven Guard"]},
    "Ivywood Dormitory":{"magic":"medium","tech":"modern","setting":"fantasy","category":"fantasy","locations":6,"npcs":8,"factions":3,
        "faction_names":["Student Council","Rival Dorm","Faculty"],
        "npc_profs":["Dorm Roommate","Resident Advisor","Rival Student","Professor","Childhood Friend","Dorm Roommate","Dorm Roommate","Campus Newspaper Editor"]},
    "Wandering Blades":{"magic":"medium","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":10,"npcs":8,"factions":3,
        "faction_names":["Adventurers' Guild","Rival Party","Ancient Order"],
        "npc_profs":["Guild Quartermaster","Rival Adventurer","Party Healer","Party Rogue","Mysterious Patron","Dungeon Warden","Old Sage","Traveling Merchant"]},
    "The Abandoned Party":{"magic":"medium","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":9,"npcs":8,"factions":3,
        "faction_names":["The Old Party","Mercenary Guild","Ancient Order"],
        "npc_profs":["Betraying Party Leader","Former Party Member","New Ally","Guildmaster","Informant","Old Rival","Village Survivor","Wandering Healer"]},
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
    "Crown & Shadows":{"magic":"none","tech":"renaissance","setting":"drama","category":"drama","locations":8,"npcs":10,"factions":4,
        "faction_names":["Royal Court","Merchant Council","Church Synod","Exiled Bloodline"],
        "npc_profs":["Monarch","Court Advisor","Spymaster","Heir Apparent","Ambassador","Noble Rival","Steward","Chronicler","Betrothed","Disgraced Knight"]},
    "The Sterling Family":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":6,"npcs":8,"factions":3,
        "faction_names":["Sterling Holdings","The Board","Estranged Kin"],
        "npc_profs":["CEO","Estranged Sibling","Family Lawyer","Rival Executive","Journalist","Housekeeper","Therapist","Business Partner"]},
    "Office Rivalry":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":6,"npcs":8,"factions":4,
        "faction_names":["Executive Board","Sales Division","HR Department","Rival Firm"],
        "npc_profs":["CEO","Rival Colleague","Office Manager","HR Director","Mentor","Love Interest","Whistleblower","Intern"]},
    "Twenty Years Gone":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":5,"npcs":6,"factions":3,
        "faction_names":["The Family","Old Friends","New Household"],
        "npc_profs":["Returning Parent","Sibling","Guardian Who Stayed","Family Friend","Therapist","Neighbor"]},
    "Blood & Loyalty":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":8,"npcs":8,"factions":4,
        "faction_names":["The Family Business","Rival Syndicate","Law Enforcement","Old Allies"],
        "npc_profs":["Family Patriarch","Underboss","Estranged Sibling","Family Lawyer","Detective","Childhood Friend","Consigliere","Informant"]},
    "Ridgewood University":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":7,"npcs":8,"factions":4,
        "faction_names":["Student Council","Greek Life","Faculty Senate","Campus Paper"],
        "npc_profs":["Class President","Rival Student","Professor","Roommate","Campus Reporter","Childhood Friend","Coach","Dean"]},
    "Second Marriage":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":5,"npcs":6,"factions":3,
        "faction_names":["The Household","Ex-Spouses","Extended Family"],
        "npc_profs":["Stepparent","Stepsibling","Biological Parent","Family Therapist","Childhood Friend","Ex-Spouse"]},
    "The Return":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":5,"npcs":6,"factions":3,
        "faction_names":["Current Relationship","Old Flame's Circle","Mutual Friends"],
        "npc_profs":["Current Partner","Returning Ex","Mutual Friend","Family Member","Rival Suitor","Confidant"]},

    # ── User-authored drama scenarios ────────────────────────────────────────
    "Liam & His Stepmom":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":5,"npcs":6,"factions":2,
        "faction_names":["The Household","University Circle"],
        "npc_profs":["Stepmom","Liam (College Student)","Family Friend","University Roommate","Neighbor","Grief Counsellor"],
        "opening":(
            "Liam is a college student who comes home from university to find his stepmom crying alone in the living room. "
            "His father passed away recently, and she is grieving deeply — she misses her husband and feels lost. "
            "Liam and his stepmom have always had a warm but slightly awkward relationship; now they must navigate grief together. "
            "The player controls Liam. The stepmom's name, appearance, and exact personality should be established through the opening conversation."
        )},

    "Liana's Three Husbands":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":5,"npcs":7,"factions":2,
        "faction_names":["The Household","Friends & Family"],
        "npc_profs":["Liana","Mark (Husband)","Alex (Husband)","John (Husband)","Marriage Counsellor","Best Friend","Sibling"],
        "opening":(
            "Liana lives in a plural marriage with three husbands: Mark, Alex, and John. "
            "Last night a heated argument broke out — one of the husbands, or possibly all three, are now angry and tense with Liana. "
            "The household is thick with unspoken words this morning. "
            "Mark tends to be calm but holds grudges quietly. Alex is more expressive — he wears his hurt openly. "
            "John is the peacekeeper of the group but even he is struggling to stay neutral after what was said. "
            "The player controls Liana as she navigates the morning after, trying to repair the fractures in her household "
            "while figuring out who she needs to reach first and what she truly wants to say."
        )},

    "Liana and Her Three Dads":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":6,"npcs":8,"factions":3,
        "faction_names":["The Family","Dad's Work World","Liana's Own Life"],
        "npc_profs":["Liana (18)","Carl (38) — Funny Dad","Steve (37) — Serious & Protective Dad","Mike (36) — Passionate Dad","Maya (37) — Mom","Liana's Best Friend","School Counsellor","Neighbour"],
        "opening":(
            "Liana is 18 years old. Her mother Maya (37) has three husbands — Carl (38), funny and light-hearted; "
            "Steve (37), serious and fiercely protective; and Mike (36), passionate and emotionally intense. "
            "All three men are successful businessmen. Despite their love for Liana, all three dads have been consumed by work "
            "for the past two years, emotionally absent and barely home. "
            "Liana feels invisible — convinced her parents simply do not love her anymore. "
            "The player controls Liana as she tries to reconnect with her family, or forge her own path without them."
        )},

    "Liam & Eve — Neighbours":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":5,"npcs":7,"factions":2,
        "faction_names":["The Neighbourhood Circle","Extended Family"],
        "npc_profs":["Liam (42) — Single Dad","Eve — Liam's Neighbour","Mia — Liam's Daughter","David — Eve's Son","Eve's Sister","Neighbourhood Friend","Mutual Friend"],
        "opening":(
            "Liam (42) is single. Years ago, his daughter Mia and Eve's son David briefly dated in high school — they knew each other "
            "through their parents' close friendship — but the young couple parted ways without drama. "
            "Five years have passed. Liam and Eve's friendship never wavered; they live in the same neighbourhood and spend most of "
            "their time together — shared dinners, morning walks, easy conversation. "
            "The line between deep friendship and something more has quietly blurred. "
            "The scenario opens at a school meeting where Liam and Eve both happen to attend. "
            "Eve's sister — mischievous and romantic — has quietly arranged for Liam and Eve to be seated together as a couple for the evening, "
            "engineering the very push neither of them would take themselves. "
            "The player controls Liam as he navigates surprise, embarrassment, and the realisation that maybe Eve's sister isn't wrong."
        )},
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
    if t.get("opening"):
        try:
            from core.lorebook import create_entry
            create_entry("Opening Scenario", t["opening"], ["opening","scenario","backstory"],
                         world_id=wid, always_active=True)
        except Exception:
            log.debug("suppressed opening lorebook entry", exc_info=True)
    try:
        from core.simulation_engine import init_market; init_market(wid)
    except Exception:
        log.debug("suppressed error", exc_info=True)
        pass
    return w
