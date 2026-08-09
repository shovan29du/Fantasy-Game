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
    "The Forgotten Twin":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":5,"npcs":7,"factions":2,
        "faction_names":["The Family","The Outside World"],
        "npc_profs":["The Player (Twin)","Elena (Twin Sister)","Mom","Dad","Grandparent","Best Friend","School Counsellor"],
        "opening":(
            "You and Elena are twins — born on the same day, raised under the same roof. "
            "But your parents have always treated you differently. "
            "Every year they celebrate Elena's birthday with a cake, gifts, and a family gathering. "
            "Your birthday passes without a word — no cake, no gift, sometimes not even a happy birthday. "
            "When Elena gets a good grade, lands a small role in a school play, or wins anything at all, "
            "your parents cheer, post about it, and call the relatives. "
            "When you achieve something — however big — it is met with silence or a subject change. "
            "You have never confronted them directly. The hurt has been building for years. "
            "Today is your shared birthday. Elena's cake is already on the table. "
            "The player is the forgotten twin. Their name, gender, and exact feelings unfold through play."
        )},
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
            "Liana is 18 years old. Her mother is Maya (37) and she has three dads — Carl (38), funny and light-hearted; "
            "Steve (37), serious and fiercely protective; and Mike (36), passionate and emotionally intense. "
            "All three dads are successful businessmen. "
            "For the past two years, all four parents — Maya and all three dads — have ignored Liana almost completely. "
            "They are physically present in the house but emotionally unreachable: "
            "no conversations, no interest in her life, no affection. "
            "Liana is convinced her entire family has stopped loving her. She feels utterly alone inside a full house. "
            "The player controls Liana. The story explores whether she confronts them, withdraws, or finds connection elsewhere — "
            "and whether her parents' silence has a reason she does not yet know."
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

    "Before Everything Breaks":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":5,"npcs":7,"factions":2,
        "faction_names":["The Inner Circle","Outsiders"],
        "npc_profs":["Lisa","User (the one who always loved her)","Mutual Friend","Neighbour","Confidant","The Secret Holder","Late-Night Caller"],
        "opening":(
            "Lisa was always your sanctuary — the one place in the world that felt safe and whole. "
            "But something has been wrong for weeks. A secret she has been carrying has slowly changed the air between you. "
            "Red wine and lies. Small ones at first, then larger silences that swallowed whole evenings. "
            "You have loved her from the beginning — the kind of love that does not know how to stop. "
            "Tonight the smell of wine lingers as you push open the door. It is 7:47 PM. The apartment is quiet. "
            "Lisa is curled on the sofa beneath the warm glow of the floor lamp, a golden shadow. "
            "Her coat is draped over the armrest. Her breathing is slow and controlled. "
            "You pause in the doorway, key still in hand. "
            "Dark red wine reflects in her pupils as her gaze finds yours. Her lips part. "
            "Her voice — low, swift, almost broken — shatters the silence: "
            "'Come here. I need to tell you something before everything breaks.' "
            "The player controls the User. What Lisa is about to confess — and what you do with it — unfolds through play."
        )},

    "Lily at the Coffee Shop":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":5,"npcs":7,"factions":3,
        "faction_names":["Lily's World","User's New Life","May's Circle"],
        "npc_profs":["Lily (21, college student)","User (the father who always loved her)","May (Lily's mother)","Lily's College Friend","Coffee Shop Regular","Mutual Acquaintance","May's New Partner"],
        "opening":(
            "User and May married young — he was 22, she was 20. Years later May gave birth to Lily. "
            "User raised Lily as his own daughter and loved her with everything he had. "
            "They were remarkably close — the kind of father-daughter bond that other people noticed and envied. "
            "What User never knew: Lily was not his biological daughter. May had been unfaithful. "
            "May grew complacent. The cheating continued. When User finally discovered the truth, they divorced. "
            "To protect herself, May told Lily terrible lies about User — that he abandoned them, that he was cruel, "
            "that the divorce was entirely his fault. Lily believed every word. She refused to see him. "
            "For years, User tried and was turned away every time. "
            "Then, when Lily was 21 and away at college, May got drunk one night and told the truth. "
            "She admitted she had cheated. She admitted the divorce was her fault. "
            "She confessed, one by one, the lies she had told Lily about the man who had always loved her. "
            "Lily is now standing outside the coffee shop where she knows User is — gathering every nerve she has "
            "to walk through that door and face the man she pushed away, the man who never stopped being her father. "
            "May has found out what Lily is doing and is already on her way to the coffee shop. "
            "The player controls Lily. What she says, what she asks, and how she holds herself in that first moment "
            "is entirely in her hands."
        )},

    "The Brother's Fiancée":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":6,"npcs":8,"factions":3,
        "faction_names":["The Mansion Circle","The Film World","Back Home"],
        "npc_profs":["User (the grounded brother)","Amanda (the fiancée)","The Hollywood Brother","Brother's Agent","Film Crew Member","Household Staff","Childhood Friend","The Late Mother's Memory"],
        "opening":(
            "You and your brother could not be more different. "
            "He went to Los Angeles to chase the camera lights and became an actor. "
            "You became an officer in the Air Force, then built a company from the ground up as an entrepreneur. "
            "He is Hollywood handsome — the kind of face that stops traffic on Sunset Boulevard. "
            "You are handsome in a different way: solid, dependable, the kind of man people trust without thinking about it. "
            "When your mother fell ill, you were the one who showed up. You rearranged your life, your career, your plans — "
            "and you cared for her every single day until the day she died. "
            "Your brother sent money occasionally and barely made it home in time for the end. "
            "A few years later, he calls. He is getting married. He wants you as his best man. "
            "You fly to Los Angeles. His mansion is exactly what you would expect — enormous, quiet, expensively perfect. "
            "Your brother is away on a shoot for a few days and asks his fiancée to welcome you. "
            "Her name is Amanda. She is an actress, and she is exactly as beautiful as you would expect "
            "someone your brother chose to be. But Amanda is more than that. "
            "There is a depth to her that surprises you — a sincerity, a quiet warmth that has nothing to do "
            "with the world your brother inhabits. "
            "You are alone in the mansion with Amanda for the next few days — "
            "the loyal brother who did everything right while his brother played movie star. "
            "The player controls the User. What happens next is entirely in your hands."
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
