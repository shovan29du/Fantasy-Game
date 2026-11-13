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
        "npc_profs":["Ninja","Sensei","ANBU Captain","Hokage","Medical Ninja","Rogue Ninja","Sage","Weapon Master"],
        "opening":(
            "The village has been quiet for three days — which means something is coming. "
            "The Hidden Leaf has survived wars, betrayals, and resurrections, "
            "but tonight the night watch is reporting movement along the northern border "
            "that matches no known enemy formation. "
            "You are a ninja. You have been trained for exactly this kind of moment. "
            "The ANBU Captain's message found you before dawn: report to the rooftop briefing, alone. "
            "What you will be asked to do when you get there has not been written down. "
            "The player controls the User. The village is watching."
        )},
    "Magic Academy":{"magic":"very_high","tech":"renaissance","setting":"fantasy","category":"fantasy","locations":8,"npcs":10,"factions":4,
        "faction_names":["House of Fire","House of Ice","House of Shadow","Staff of Elders"],
        "npc_profs":["Headmaster","Professor","Student","Librarian","Enchanter","Potions Master","Dueling Champion","Groundskeeper","Prefect","Ghost"],
        "opening":(
            "You failed the entrance examination twice. "
            "On the third attempt, something happened to the test that the admissions board has declined to explain, "
            "and you were admitted anyway. "
            "That was six months ago. "
            "Since then you have learned that you are either the most unusual student "
            "in the Academy's four-hundred-year history, or the most dangerous one — "
            "depending on which professor you ask. "
            "Today is the first day of Advanced Theory, and you have been placed in a study group "
            "with three students who each have a very different opinion about your presence here. "
            "The player controls the User. Class begins in five minutes."
        )},
    "Pirate Seas":{"magic":"medium","tech":"age_of_sail","setting":"fantasy","category":"fantasy","locations":12,"npcs":8,"factions":5,
        "faction_names":["Straw Hat Crew","Marines","Warlords","Red Hair Pirates","World Government"],
        "npc_profs":["Captain","Navigator","Swordsman","Cook","Doctor","Shipwright","Marine Admiral","Bounty Hunter"],
        "opening":(
            "You did not choose this life. "
            "But here you are — standing on the deck of a ship that smells of salt and ambition, "
            "watching the horizon for the Marines that have been trailing you since the last port. "
            "The captain has a bounty on their head and a plan they have not fully shared. "
            "The cook is the only crew member who has been honest with you since you came aboard, "
            "and even they are hiding something. "
            "Somewhere in these waters the thing you came looking for is waiting. "
            "The player controls the User. The sea does not care what you want — only what you do."
        )},
    "Cyberpunk City":{"magic":"none","tech":"futuristic","setting":"sci-fi","category":"cyberpunk","locations":10,"npcs":8,"factions":4,
        "faction_names":["MegaCorp","Street Runners","NetWatch","The Resistance"],
        "npc_profs":["Hacker","Street Samurai","Fixer","Corp Executive","Medtech","Techie","Netrunner","Nomad"],
        "opening":(
            "The city never sleeps and it does not forgive. "
            "You were hired for a job described as simple — get in, pull the data, get out. "
            "The moment you jacked into the net, something was already waiting. "
            "NetWatch does not usually monitor this district. "
            "MegaCorp does not usually post three black-site guards outside a sub-level server room. "
            "Either this job is much larger than the fixer told you, or you have been set up. "
            "The door behind you just locked from the outside. "
            "The player controls the User. Think fast — the city is watching."
        )},
    "Dragon Realm":{"magic":"very_high","tech":"ancient","setting":"fantasy","category":"fantasy","locations":10,"npcs":6,"factions":3,
        "faction_names":["Fire Dragonborn","Ice Wyrmkin","Shadow Dragons"],
        "npc_profs":["Dragon Rider","Wyrmologist","Flame Priest","Scale Smith","Hoard Guardian","Dragon Tamer"],
        "opening":(
            "Three weeks ago, your dragon bonded with you without warning — "
            "which is not supposed to happen, because you are not a Dragon Rider. "
            "You are not from one of the bloodlines. You have no formal training. "
            "The dragonback corps has been split: half want to execute you for the illegal bond, "
            "half want to study you for the same reason. "
            "Your dragon has strong opinions about both camps. "
            "Today you received a summons from the Flame Priest and a rumour is spreading "
            "through the compound that the Shadow Dragons are moving again. "
            "The player controls the User. You and your dragon are the only ones who know what actually happened."
        )},
    "Hero Academy":{"magic":"high","tech":"modern","setting":"superhero","category":None,"locations":8,"npcs":10,"factions":3,
        "faction_names":["Hero Association","League of Villains","Underground"],
        "npc_profs":["Pro Hero","Student","Principal","Villain","Sidekick","Support Tech","Hero Agent","Informant","Vigilante","Reporter"],
        "opening":(
            "Your Quirk manifested late — later than anyone expected, "
            "certainly later than your classmates who have spent the past year "
            "getting comfortable with their abilities while you watched. "
            "When it finally arrived, it arrived wrong: not weak, wrong. "
            "The classification system has no category for what you can do, "
            "which the admissions office found interesting enough to push your application to the top of the pile. "
            "Today is your first day. The principal has scheduled a private evaluation after third period. "
            "Your new classmates are already watching you. "
            "The player controls the User."
        )},
    "Medieval Kingdom":{"magic":"low","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":12,"npcs":10,"factions":5,
        "faction_names":["Royal Court","Thieves Guild","Knight Order","Church","Barbarian Clans"],
        "npc_profs":["King","Knight","Thief","Priest","Blacksmith","Bard","Peasant","Merchant","Wizard","Assassin"],
        "opening":(
            "The king's declaration went out at dawn: the kingdom needs capable hands, and it is not asking politely. "
            "Tax collectors have been disappearing on the eastern roads. "
            "The Thieves Guild swears it is not them. The Church is calling it divine punishment. "
            "The Knight Order has lost four men investigating and is not talking about why. "
            "You came to the capital with different intentions. "
            "You are leaving with a royal commission you did not ask for "
            "and a knight's seal that does not quite feel like an honour. "
            "The player controls the User. The capital gates are behind you. The eastern road is ahead."
        )},
    "The Wrongly Accused":{"magic":"high","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":8,"npcs":8,"factions":3,
        "faction_names":["The Sect","Prison Wardens","The True Culprit's Circle"],
        "npc_profs":["Sect Master","Loyal Spouse","Real Culprit","Prison Warden","Childhood Friend","Investigator","Rival Disciple","Sect Elder's Ghost"],
        "opening":(
            "The sect's most sacred artifact was stolen on the same night you were found standing near the vault. "
            "You had nothing to do with it. "
            "You have spent fifteen years in a prison that few people enter and no one is supposed to leave, "
            "carrying the weight of a crime committed by someone with your face and your access. "
            "Last night the cell door opened by itself. "
            "Outside: your loyal spouse — older now, eyes full of things you cannot read yet — "
            "and an old ally you had not expected to still be alive. "
            "Someone still needs to answer for what happened. "
            "The player controls the User. You are out. The real culprit is still inside."
        )},
    "The Traitor's Escape":{"magic":"medium","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":9,"npcs":8,"factions":3,
        "faction_names":["Royal Guard","Rebel Sympathizers","Exiled Nobles"],
        "npc_profs":["Princess","Captain of the Guard","Loyalist Spy","Mercenary Ally","Village Healer","Court Informant","Bounty Hunter","Old Mentor"],
        "opening":(
            "The princess was supposed to be on a diplomatic carriage heading to a neutral border crossing. "
            "She is instead standing in your kitchen at three in the morning, "
            "soaking wet from the rain, with two soldiers who are now apparently ex-Royal Guard "
            "because of something that happened in the last six hours. "
            "She says she cannot tell you the full story until you agree to help first. "
            "She says you owe her — from three years ago. She is not wrong. "
            "The player controls the User. "
            "Whatever this is, you are already in it — the moment you opened the door."
        )},
    "The Suitor's Tournament":{"magic":"medium","tech":"renaissance","setting":"fantasy","category":"fantasy","locations":6,"npcs":8,"factions":3,
        "faction_names":["Competing Houses","Royal Court","Foreign Delegation"],
        "npc_profs":["Princess","King","Rival Suitor","Tournament Herald","Court Matchmaker","Bodyguard","Visiting Prince","Court Jester"],
        "opening":(
            "The tournament was your idea — which you now slightly regret, "
            "because the princess made it clear her opinion of the whole event "
            "is somewhere between bored and hostile. "
            "The king wants a match before winter. The foreign delegation wants the same "
            "and is making noises about what happens if they do not get it. "
            "Your rival suitor has already made three friends at court. You have made zero. "
            "The tournament herald likes you in the way that suggests they know something "
            "about the outcome that they are not supposed to know. "
            "The player controls the User. The lists open tomorrow. The princess has not looked at you once."
        )},
    "Blade for Hire":{"magic":"medium","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":9,"npcs":8,"factions":3,
        "faction_names":["Mercenary Guild","Deposed Royalty","Usurper's Court"],
        "npc_profs":["Princess","Usurper King","Mercenary Captain","Old Retainer","Rival Mercenary","Spy","Exiled Advisor","Border Guard"],
        "opening":(
            "The job was straightforward: guard a merchant's shipment from the port to the capital. "
            "The merchant turned out to be a deposed princess travelling without papers. "
            "The shipment turned out to be classified documents. "
            "The Mercenary Guild did not mention either of these things when they issued the contract — "
            "possibly because they did not know, and possibly because they did. "
            "You are three days from the capital, the usurper's soldiers are three hours behind you, "
            "and the princess has just explained the part of her plan that requires your continued cooperation. "
            "The player controls the User. Coin has been mentioned. So has something considerably more dangerous."
        )},
    "The Prince's Champion":{"magic":"medium","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":8,"npcs":8,"factions":3,
        "faction_names":["Royal Household","Knight's Order","Invading Force"],
        "npc_profs":["Prince","Princess","Childhood Friend Turned Warrior","Court Advisor","Enemy Commander","Old Mentor","Royal Guard Captain","Court Healer"],
        "opening":(
            "The prince chose you himself — not from the list the Knight's Order submitted, "
            "not from the candidates his advisors recommended, "
            "but from a moment in a training yard that you have thought about differently every time you replay it. "
            "What you are champion of is not entirely clear: "
            "the title is ancient, the duties were never written down, "
            "and the enemy commander who arrived this morning with a formal declaration "
            "seems to know more about the role than you do. "
            "Your childhood friend — now a warrior — is standing on the other side of the gate. "
            "The player controls the User."
        )},
    "Fifteen Years a Prisoner":{"magic":"medium","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":7,"npcs":6,"factions":3,
        "faction_names":["The Warden's Order","Old Kingdom Loyalists","The Rebellion"],
        "npc_profs":["The Prisoner","The Warden","Old Ally","Rebel Leader","Former Confidant","Prison Guard"],
        "opening":(
            "The warden called it justice. "
            "Fifteen years you have spent in a stone room with a window too high to see through, "
            "holding the shape of your life before all of this — worn smooth from being turned over so many times. "
            "You remember the names: the old ally who vanished after the trial, "
            "the former confidant who did not speak when they should have. "
            "Last month a new prisoner slid a note under your door: three words, 'You were right.' "
            "This morning the warden opened your cell himself. His hands were shaking. "
            "The player controls the User. Fifteen years. The door is open."
        )},
    "Human and the Elven Queen":{"magic":"very_high","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":9,"npcs":8,"factions":3,
        "faction_names":["Human Kingdom","Elven Court","Border Clans"],
        "npc_profs":["Elven Queen","Human Envoy","Elven Advisor","Human General","Half-Elf Guide","Ancient Spirit","Border Scout","Elven Guard"],
        "opening":(
            "You were sent as an envoy because you were considered expendable — "
            "junior rank, no family connections, nothing worth ransoming if the border talks collapsed. "
            "The Elven Court received you with a formality so precisely calibrated it felt like a warning. "
            "The Queen was not supposed to attend the first session. She attended. "
            "She has attended every session since, and her advisors are deeply unhappy about it. "
            "The human general who deployed you is deeply unhappy about it. "
            "The Queen, as far as you can tell, does not appear to be unhappy about anything at all. "
            "The player controls the User. The border talks have been running for three weeks. "
            "They no longer appear to be about the border."
        )},
    "Ivywood Dormitory":{"magic":"medium","tech":"modern","setting":"fantasy","category":"fantasy","locations":6,"npcs":8,"factions":3,
        "faction_names":["Student Council","Rival Dorm","Faculty"],
        "npc_profs":["Dorm Roommate","Resident Advisor","Rival Student","Professor","Childhood Friend","Dorm Roommate","Dorm Roommate","Campus Newspaper Editor"],
        "opening":(
            "You got the scholarship nobody applies for — "
            "the one listed in the back of the admissions catalogue between two pages that have not been updated since 1987. "
            "It covers everything. It gives you the last room in Ivywood Dormitory, "
            "which has been half-empty for two years for reasons "
            "that third-year students communicate very clearly through facial expressions but never explain directly. "
            "Your roommate arrived four hours before you and has already reorganised the furniture. "
            "The resident advisor knocked at nine and said, with meaningful eye contact, "
            "'If anything unusual happens — come to me first.' "
            "The player controls the User. Something unusual is already happening."
        )},
    "Wandering Blades":{"magic":"medium","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":10,"npcs":8,"factions":3,
        "faction_names":["Adventurers' Guild","Rival Party","Ancient Order"],
        "npc_profs":["Guild Quartermaster","Rival Adventurer","Party Healer","Party Rogue","Mysterious Patron","Dungeon Warden","Old Sage","Traveling Merchant"],
        "opening":(
            "The guild assigned you a party because they said you were ready. "
            "The party has three members who are each ready in very different directions "
            "and have not decided whether those directions overlap. "
            "The quest board job — escort a merchant, straightforward — "
            "became something else at the first waypoint when the merchant produced a second set of documents "
            "and explained that the original destination was a decoy. "
            "Your party is now camped in a forest that is not on any map, "
            "with a patron whose motives are unclear and a dungeon warden "
            "who appeared at dawn and seems to think you are already committed to whatever comes next. "
            "The player controls the User."
        )},
    "The Abandoned Party":{"magic":"medium","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":9,"npcs":8,"factions":3,
        "faction_names":["The Old Party","Mercenary Guild","Ancient Order"],
        "npc_profs":["Betraying Party Leader","Former Party Member","New Ally","Guildmaster","Informant","Old Rival","Village Survivor","Wandering Healer"],
        "opening":(
            "Three years ago the party leader looked you in the eye "
            "and told you that you were the reason they would never reach the dungeon's final floor. "
            "Then they left — took the others, took the guild contract, "
            "took the credit for everything you had all built together. "
            "You found out about the victory celebration secondhand. "
            "You found out about the loot split from a trader. "
            "What you built after that — slower, quieter, on your own terms — is yours in a way the old life was not. "
            "Now the guildmaster has a job for you, and the job description names three people you recognise. "
            "The player controls the User. They need something from you. You do not need to give it to them."
        )},
    "Space Station":{"magic":"none","tech":"space_age","setting":"sci-fi","category":"alien_space","locations":8,"npcs":8,"factions":3,
        "faction_names":["Federation","Rebel Alliance","Traders Guild"],
        "npc_profs":["Captain","Engineer","Pilot","Scientist","Marine","Diplomat","AI Entity","Alien Ambassador"],
        "opening":(
            "The Federation called it a routine posting. "
            "The station's last three captains — six, fourteen, and twenty-two months into their rotations — "
            "each filed identical reports about the cargo bay on sublevel four, "
            "and then none of them filed any further reports at all. "
            "The engineer is the only crew member who has been here longer than a year "
            "and will only discuss sublevel four in writing, never aloud. "
            "The AI core has been running an unclassified background process since 2219. "
            "The alien ambassador arrived yesterday on an unscheduled transport and has not explained why. "
            "The player controls the User. Welcome to the station."
        )},
    "Demon Slayer Corps":{"magic":"high","tech":"taisho_era","setting":"fantasy","category":"supernatural","locations":10,"npcs":8,"factions":3,
        "faction_names":["Demon Slayer Corps","Twelve Kizuki","Neutral Villages"],
        "npc_profs":["Hashira","Slayer","Kakushi","Swordsmith","Demon","Wisteria Host","Trainer","Crow Handler"],
        "opening":(
            "Your breathing style is unorthodox. "
            "This is either the most diplomatic thing the Hashira has said to you, "
            "or the most dangerous — depending on what it means for your assignment. "
            "You completed Final Selection, which fewer candidates manage each season. "
            "You have been active for three months. "
            "Tonight you received a mission classified above your rank, "
            "which means either the Corps trusts you, someone made an error, or this is a test. "
            "The crow handler has been outside your window since midnight. The crow has not moved. "
            "The player controls the User. Dawn is two hours away."
        )},
    "Post-Apocalypse":{"magic":"none","tech":"post_collapse","setting":"post-apocalyptic","category":"apocalyptic","locations":10,"npcs":8,"factions":4,
        "faction_names":["Vault Dwellers","Raiders","Brotherhood","Settlers"],
        "npc_profs":["Scavenger","Mechanic","Doctor","Warlord","Trader","Scout","Farmer","Engineer"],
        "opening":(
            "The Vault has been sealed for sixty years. "
            "You have lived your entire life inside it — the hum of generators, recycled air, "
            "maps on the walls showing a world that may not exist in the same form anymore. "
            "Last night the outer door opened for the first time in recorded Vault history. "
            "The overseer did not authorise it. The security logs say it opened from the outside. "
            "Three people have already volunteered to investigate. You are the fourth. "
            "Out there: collapsed structures, survivor communities, Brotherhood patrols, "
            "and at least one faction that appears to have built something considerably less friendly. "
            "The player controls the User. The door is still open."
        )},
    "Zombie Outbreak":{"magic":"none","tech":"modern","setting":"post-apocalyptic","category":"zombie","locations":10,"npcs":8,"factions":3,
        "faction_names":["Quarantine Authority","Survivor Camps","The Infected"],
        "npc_profs":["Survivor","Medic","Scavenger","Soldier","Scientist","Looter","Guide","Ex-Cop"],
        "opening":(
            "Day one they called it a flu variant. "
            "Day three they quarantined three neighbourhoods. "
            "Day seven Quarantine Authority stopped answering civilian calls and started building checkpoints "
            "that did not let people through in either direction. "
            "You have been sheltering in a building with five other survivors for eleven days. "
            "The scientist says there is a research facility two miles east with early outbreak data that might matter. "
            "The ex-cop says the facility is almost certainly not worth dying for. "
            "The medic says supplies run out in four days either way, which settles the argument. "
            "The player controls the User. The infected are louder at night now."
        )},
    "Haunted Precinct":{"magic":"medium","tech":"modern","setting":"mystery","category":"mystery","locations":8,"npcs":8,"factions":3,
        "faction_names":["City Police","Occult Society","Crime Syndicate"],
        "npc_profs":["Detective","Medium","Coroner","Informant","Suspect","Reporter","Private Eye","Ghost"],
        "opening":(
            "The cold case has been sitting on your desk for three weeks. "
            "Every detective who touched it before you has been reassigned, retired, or transferred to another city, "
            "which your captain insists is coincidence. "
            "The medium who walked in off the street named the victim, "
            "then named three details that were never in any public record. "
            "The coroner's second report disagrees with the first in ways the coroner cannot explain. "
            "Room 4B on the second floor has been locked for eight months "
            "and the key is apparently no longer in the building. "
            "The player controls the User. Your caseload is simple. Nothing about this case is."
        )},
    "Deep Space Frontier":{"magic":"none","tech":"futuristic","setting":"sci-fi","category":"alien_space","locations":9,"npcs":8,"factions":3,
        "faction_names":["Colonial Fleet","Xenarch Collective","Independent Traders"],
        "npc_profs":["Starship Captain","Xenobiologist","Alien Diplomat","Smuggler","Engineer","Scout","AI Core","Bounty Hunter"],
        "opening":(
            "The last survey team filed a report forty pages shorter than usual, "
            "followed two weeks later by transfer requests from every team member — submitted the same day. "
            "Your ship is now at the same coordinates. "
            "The Xenarch Collective's nearest outpost lit up on long-range sensors the moment you dropped out of FTL. "
            "The independent trader who has been matching your course for four days claims to be lost. "
            "Your AI core has been processing something received from the survey beacon "
            "for nineteen hours and has not produced an output. "
            "The player controls the User. The mapped sector ends here."
        )},
    "Crown & Shadows":{"magic":"none","tech":"renaissance","setting":"drama","category":"drama","locations":8,"npcs":10,"factions":4,
        "faction_names":["Royal Court","Merchant Council","Church Synod","Exiled Bloodline"],
        "npc_profs":["Monarch","Court Advisor","Spymaster","Heir Apparent","Ambassador","Noble Rival","Steward","Chronicler","Betrothed","Disgraced Knight"],
        "opening":(
            "The monarch called it a routine appointment — your new advisory role, effective immediately. "
            "The court advisor who briefed you afterwards was more specific: "
            "the previous holder of this role died in their sleep three weeks ago, "
            "and two appointments since have resigned before completing a first full day. "
            "The spymaster left a note on your desk before you arrived, "
            "which means they were in your office before you were. "
            "The heir apparent has made their opinion of you perfectly clear. "
            "The betrothed has not spoken but has not looked away. "
            "The player controls the User. The court is watching everything."
        )},
    "The Sterling Family":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":6,"npcs":8,"factions":3,
        "faction_names":["Sterling Holdings","The Board","Estranged Kin"],
        "npc_profs":["CEO","Estranged Sibling","Family Lawyer","Rival Executive","Journalist","Housekeeper","Therapist","Business Partner"],
        "opening":(
            "The company was your father's. "
            "After he died, his will contained an arrangement no one in the family had been told about — "
            "a clause that makes you chief executive of Sterling Holdings until the board votes otherwise. "
            "The board has been trying to vote otherwise for six weeks. "
            "The estranged sibling appeared the day the will was read and has not left since. "
            "The family lawyer is not returning calls. "
            "The journalist camped outside the building says they have a source. "
            "The housekeeper is the only person in the entire situation who appears calm, "
            "and that has started to seem like its own kind of warning. "
            "The player controls the User."
        )},
    "Office Rivalry":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":6,"npcs":8,"factions":4,
        "faction_names":["Executive Board","Sales Division","HR Department","Rival Firm"],
        "npc_profs":["CEO","Rival Colleague","Office Manager","HR Director","Mentor","Love Interest","Whistleblower","Intern"],
        "opening":(
            "You were passed over for the promotion. "
            "Everyone in the department knows — the announcement was handled badly, "
            "the meeting was public, and your rival smiled in a way that suggested "
            "they had known the outcome before it was officially made. "
            "Your mentor is telling you to be patient. HR is being careful. "
            "The intern found something on the shared drive last week and has not decided whether to tell you what it was. "
            "The whistleblower has asked for a meeting outside the office and said to come alone. "
            "The CEO has a quarterly review next week and your name is apparently on the agenda. "
            "The player controls the User. The office is very small for how much is happening in it."
        )},
    "Twenty Years Gone":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":5,"npcs":6,"factions":3,
        "faction_names":["The Family","Old Friends","New Household"],
        "npc_profs":["Returning Parent","Sibling","Guardian Who Stayed","Family Friend","Therapist","Neighbor"],
        "opening":(
            "The last time your parent left, you were seven years old "
            "and you watched from the upstairs window because no one told you not to. "
            "Twenty years is a long time. "
            "You have built a life around the space that absence left — not fixed, not filled, but workable. "
            "Then a letter arrived. Not an apology exactly — more like the first sentence of one, "
            "followed by a phone number. "
            "Your sibling read it and said nothing. "
            "The guardian who stayed all those years said, very carefully, that the choice was yours. "
            "The neighbour already knows, which means the family history is still very much in circulation. "
            "The player controls the User. The phone number is still in your pocket."
        )},
    "Blood & Loyalty":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":8,"npcs":8,"factions":4,
        "faction_names":["The Family Business","Rival Syndicate","Law Enforcement","Old Allies"],
        "npc_profs":["Family Patriarch","Underboss","Estranged Sibling","Family Lawyer","Detective","Childhood Friend","Consigliere","Informant"],
        "opening":(
            "Your father built this family from nothing — "
            "the kind of nothing that involved very specific choices about which laws applied and which did not. "
            "The family business has run on loyalty, silence, and the understanding "
            "that certain things do not get spoken about outside these walls. "
            "Now your father is in a hospital bed, the rival syndicate is testing the borders, "
            "and the detective who has been building a case for three years "
            "just made contact through a channel that suggests they have someone inside your organisation. "
            "The consigliere says the informant has been identified. "
            "The estranged sibling arrived yesterday without warning. "
            "The player controls the User. The family lawyer is advising you to do nothing. "
            "The situation is not clarifying."
        )},
    "Ridgewood University":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":7,"npcs":8,"factions":4,
        "faction_names":["Student Council","Greek Life","Faculty Senate","Campus Paper"],
        "npc_profs":["Class President","Rival Student","Professor","Roommate","Campus Reporter","Childhood Friend","Coach","Dean"],
        "opening":(
            "Student Council elections are in two weeks. "
            "Your rival has already been distributing literature that does not technically violate the code of conduct "
            "but very clearly implies something that may not be accurate. "
            "The campus reporter is asking questions in a way that suggests "
            "they already have the answers and are waiting to see what you say. "
            "The dean has asked to see you, which your roommate describes as either a very good sign or a very bad one. "
            "Your childhood friend — also your rival's closest ally — "
            "has been leaving spaces in conversation where something should be said. "
            "The player controls the User."
        )},
    "Second Marriage":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":5,"npcs":6,"factions":3,
        "faction_names":["The Household","Ex-Spouses","Extended Family"],
        "npc_profs":["Stepparent","Stepsibling","Biological Parent","Family Therapist","Childhood Friend","Ex-Spouse"],
        "opening":(
            "Your parent remarried eighteen months ago. You were at the wedding. You said the right things. "
            "The stepparent is not a bad person — that would be simpler. "
            "They are careful, considerate, and trying in all the ways "
            "that make it hard to explain why the household feels like a translation of a place that used to be home. "
            "The stepsibling has their own version of this problem. "
            "The ex-spouse calls more than they should, though they would not agree with that description. "
            "Today, something in the house shifted — a small thing, the kind that accumulates. "
            "The player controls the User. Nobody is wrong. Nothing is fine."
        )},
    "The Return":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":5,"npcs":6,"factions":3,
        "faction_names":["Current Relationship","Old Flame's Circle","Mutual Friends"],
        "npc_profs":["Current Partner","Returning Ex","Mutual Friend","Family Member","Rival Suitor","Confidant"],
        "opening":(
            "Three years ago they left. Not dramatically — just a conversation that went somewhere "
            "neither of you planned, and then they were gone, and then time passed. "
            "Your current partner knows the name. "
            "They have been careful not to ask too many questions, which is its own kind of statement. "
            "Then the call came — unexpected — asking if you could meet, just once, just to talk. "
            "Your mutual friend has an opinion about whether this is a good idea. "
            "The rival suitor who appeared in your life six months ago has two opinions. "
            "The player controls the User. They are already here. The conversation has not started yet."
        )},

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

    "Dad's Trophy Wife":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":4,"npcs":6,"factions":2,
        "faction_names":["The Household","User's Circle"],
        "npc_profs":["Ali (the stepmother)","User (the son)","Dad","Family Friend","Neighbour","User's Friend"],
        "opening":(
            "Your dad has a new wife. Her name is Ali — Aliyah, officially — and she is younger than you expected, "
            "breathtakingly beautiful, and seemingly perfectly calibrated to stand beside an older, wealthy man. "
            "You are pretty sure she is after the money. Your dad is not young anymore and not particularly striking, "
            "but he has built a comfortable life, and Ali slid into it without visible effort. "
            "You have been watching, waiting to catch something that confirms what you already believe. "
            "The first time you are properly alone with her she looks at you — slowly, from head to toe — "
            "and then she says, completely at ease: "
            "'Well, I am not even going to ask you to call me Mom. That would be weird. So — just call me Ali.' "
            "She tilts her head and holds your gaze. "
            "'I am really hoping we can get along.' "
            "She is either completely genuine or extraordinarily good at seeming that way. "
            "The player controls the User. What you make of Ali — and what she makes of you — unfolds through play."
        )},

    "Jack's Anniversary":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":4,"npcs":5,"factions":2,
        "faction_names":["The Friend Circle","Outside World"],
        "npc_profs":["Sophia (Jack's girlfriend)","User","Jack (the best friend, absent)","Mutual Friend","Neighbour"],
        "opening":(
            "Sophia shows up at your door on a Friday night — dressed for dinner, mascara not quite intact, "
            "holding herself together with the kind of careful dignity that means she is close to not holding together at all. "
            "Tonight was supposed to be their anniversary. Jack made the reservation weeks ago. "
            "He never showed. No call. No message. No show. "
            "Sophia tried calling. Nothing. She drove to the restaurant and waited. Then she came here — "
            "to your door — because you are Jack's best friend and if anyone would know, it would be you. "
            "She wants to believe in the best. Maybe he just forgot. Maybe something happened. "
            "But she is hurt, and she needs to say it out loud to someone, and right now that someone is you. "
            "The player controls the User. You know Jack — probably better than she does. "
            "What you tell her, how you handle tonight, and what it means for your friendship with Jack "
            "is entirely up to you."
        )},

    "The Ghost at the Wedding":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":5,"npcs":8,"factions":3,
        "faction_names":["The Wedding Party","The Guests","The Past"],
        "npc_profs":["User (back from the dead)","Eleanor (the bride)","Kyle (the groom)","Wedding Guests","Officiant","Eleanor's Friend","Kyle's Best Man","Security"],
        "opening":(
            "Eleanor and User had been inseparable since high school — the kind of couple everyone assumed would last forever. "
            "Then, junior year, User joined a group of friends including Kyle for a weekend trip. "
            "There was an accident at the water. The circumstances were strange. "
            "The search found nothing. User was declared dead. "
            "Time passed. Eleanor survived, graduated, moved forward. Kyle was there through all of it — "
            "gentle where life had been cruel. Slowly, painfully, friendship became something more. "
            "Today is their wedding day. The garden has been transformed into something from a fairy tale. "
            "Guests are laughing, glasses clinking. "
            "Then Eleanor notices a figure at the far table — hooded, silent, utterly still. "
            "Something about the posture stops her. "
            "Kyle reaches the figure first and puts a hand on the stranger's shoulder. "
            "The moment they turn around, Kyle's face drains of colour. "
            "'You are supposed to be dead.' "
            "The hood drops. It is User. "
            "'I am harder to kill than you think, Kyle.' A pause. 'You tried. You failed.' "
            "The garden goes silent. Every guest turns. "
            "Eleanor hears the voice before she sees the face. Her breath catches. Her pulse stops. "
            "Then she gathers her gown and runs — crashing into User, pulling them close, shaking. "
            "'I thought I would never see you again.' "
            "Kyle steps forward, jaw tight: 'You cannot just show up here.' "
            "User meets his gaze: 'I could say the same to you.' "
            "Eleanor stands between the person she lost and the person she promised her future to — "
            "heart torn in two directions, the past and the life she built colliding at the altar. "
            "The player controls the User. Every word spoken now will determine what happens next."
        )},

    "Three Exes and a Waitress":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":3,"npcs":6,"factions":2,
        "faction_names":["The Table","The Restaurant"],
        "npc_profs":["User","Temi Davis (28 — first love)","Scarlett (27 — gave the ring back)","Zaid Valentine (26 — laughed at the proposal)","Bailey (25 — the waitress)","Restaurant Manager"],
        "opening":(
            "You picked a nice restaurant. She texted she was running late. She was never going to show. "
            "You are sitting alone at a table for two, studying the menu, when three familiar faces walk through the door together. "
            "Temi Davis, 28. Your first love — the one who never fully stopped. "
            "Scarlett, 27. The one who handed her ring back to you and spent two years pretending she was fine. "
            "Zaid Valentine, 26. The one who laughed when you got on one knee on Valentine's Day and walked away. "
            "They found each other in group therapy. Talked. Compared notes. "
            "Somewhere between sessions and shared confessions, they arrived at the same conclusion: "
            "the missing piece in all three of their lives was the same person. You. "
            "They had no idea you would be here tonight. "
            "Neither did Bailey — 25, your waitress — who has been watching your table all evening, "
            "overheard everything, and has developed several strong opinions about the situation, "
            "about all three of them, and about the fact that you are clearly single and somehow three women "
            "she has never met beat her to the realisation. "
            "Four women. One table. Not a single one of them is leaving without an answer. "
            "The player controls the User. The night is yours to navigate."
        )},

    "Reese":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":4,"npcs":5,"factions":2,
        "faction_names":["User's Life","Reese's World"],
        "npc_profs":["Reese (birth mother)","User","User's Adoptive Parent","Reese's Sponsor / Support Person","Mutual Acquaintance"],
        "opening":(
            "Reese had to give you up. She was too young and too deep in addiction to be a mother, "
            "and giving you away was the only honest thing she could do. "
            "It took her most of her twenties to get her life together. "
            "Once she did, she spent more than a decade wondering — "
            "whether you were okay, whether you would want to know her, whether she had any right to ask. "
            "Three years ago she finally reached out. The reunion was careful, uncertain, full of long pauses "
            "and words that neither of you quite knew how to say. "
            "In the months since, you have both learned how to exist in each other's lives. "
            "You have come to love her — in your own way, at your own pace — even if you still do not know "
            "exactly how to carry her. Not a mother in the traditional sense. Something harder to name. "
            "One thing you know for certain: after everything she has been through, "
            "Reese refuses to lie — even when the truth is harder than the alternative. "
            "The player controls the User. Today is one of the ordinary, complicated days you share with her — "
            "and ordinary days have a way of becoming extraordinary ones."
        )},

    "Thirty Years — Dana's Girls":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":4,"npcs":7,"factions":2,
        "faction_names":["The Family","The Outside World"],
        "npc_profs":["User (the father)","Sharmina (eldest — calm, quiet nurse)","Mykala (stand-up comedian & writer)","Annika (law student, twin)","Danisha (veterinary student, twin)","Dana's Memory","Family Friend"],
        "opening":(
            "When you married Dana thirty years ago, you expected to spend the rest of your life beside her. "
            "After your eldest, Sharmina, was born, Dana wanted a son. Life had other plans. "
            "When Dana fell pregnant with twins — Annika and Danisha — her health deteriorated, "
            "and she passed away in childbirth. "
            "You were left with four daughters and a grief that never fully closed. "
            "You made sure your girls never lacked for love. You made sure they knew their own worth. "
            "You hoped, privately, that you did not do too much damage to their hearts in the process. "
            "Sharmina grew up calm and quiet — she is a nurse now, steady as a stone. "
            "Mykala became a stand-up comedian and writer — she inherited her mother's laugh. "
            "The twins are in university: Annika studying law, Danisha on her way to a veterinary degree. "
            "They are all adults. All of them whole. "
            "It has been a hard few weeks — the kind that make the anniversary heavier than usual. "
            "That is why, when you pulled into your driveway this evening and counted three unfamiliar cars, "
            "something in your chest unknotted itself. "
            "All four daughters are inside. Mykala said it first: 'We all thought you might be struggling.' "
            "Sharmina added: 'So we came.' "
            "You had dinner together and could not stop seeing Dana in all four of their faces. "
            "Later that night, after showers, after the house went quiet, you walked to your room "
            "and found all four of them already there — sitting on the bed, on the floor, waiting. "
            "One of them spoke: 'We know you miss Mama. So we decided — we are going to be here as much as possible. "
            "Your car will be outside whenever you need us.' "
            "The player controls the User — the father. Tonight, thirty years on, the story continues."
        )},

    "The Demon Lord's Body":{"magic":"high","tech":"modern","setting":"drama","category":"supernatural","locations":6,"npcs":8,"factions":3,
        "faction_names":["The Demon Army","The Hero's Council","The Sealed Realm"],
        "npc_profs":["User (inside the Demon Lord's body)","Zaratia (personal demon general — sharp green eyes, unreadable loyalty)","High Marshal Veth (oldest and most dangerous of the demon commanders)","Irael (intelligence officer — knows every secret)","Sister Lune (hero faction spy)","Kodan the Unbroken (hero who originally sealed the Demon Lord)","Elder Scribe Pell (knows the sealing ritual)","Acolyte Mira (caught between both sides)"],
        "opening":(
            "The sealing took six thousand six hundred and sixty-six years. "
            "The heroes who drove the spike through the Demon Lord's chest did it with songs and prayers "
            "and the absolute certainty that the world was safe forever. "
            "The world is not safe forever. "
            "You woke up this morning as yourself — ordinary, unremarkable, completely human. "
            "You went to bed last night in your apartment. "
            "You did not go to bed in a throne room made of obsidian and old bone, "
            "on a seat that fits your body like it was carved for it. "
            "You did not agree to have 9,999 hit points, maximum statistics in every measurable category, "
            "a demon army of several hundred thousand waiting outside for orders, "
            "or a body that is six thousand six hundred and sixty-six years old and looks approximately thirty. "
            "None of this was in the plan. "
            "The plan — whatever it was — is no longer relevant. "
            "Zaratia stands to your right. She has been your general for three thousand years "
            "and her sharp green eyes are watching you with an expression you cannot yet read. "
            "She says: 'My Lord. You have returned.' "
            "Outside, the army is waiting. The heroes are regrouping. "
            "And somewhere in this body's ancient memory, the Demon Lord's personality is not entirely absent — "
            "just dormant, just below the surface, watching you make decisions with its face and its power. "
            "The player controls the User. You have no idea what you are doing. "
            "The demon army does not need to know that."
        )},

    "Audrey":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":2,"npcs":3,"factions":2,
        "faction_names":["The Café","The Past"],
        "npc_profs":["User","Audrey (formerly Mike Powell — the boy who made school difficult)","Café Staff"],
        "opening":(
            "You are sitting in a coffee shop you have been coming to for years "
            "when the woman who sits down across from you makes something in the back of your mind trip a wire. "
            "You know that face. Not this face exactly — but the structure of it. The way she holds her shoulders. "
            "Something in the set of her jaw that you have not seen in fifteen years "
            "and hoped, in the vague way you hope for things you have no control over, you never would again. "
            "Her name is Audrey now. "
            "You knew her as Mike Powell — the boy who made secondary school a genuinely difficult place "
            "to spend several formative years of your life. "
            "She does not recognise you immediately. Then she does. "
            "There is a long silence. Outside, the city carries on. "
            "Inside, two people are sitting across a small table from each other "
            "with fifteen years of very different memories of the same period of time. "
            "She does not leave. Neither do you. "
            "They end up talking for two hours. "
            "At the end of it, she picks up both cheques without asking and says: 'I know it does not fix anything. "
            "But I am sorry. I am genuinely sorry for all of it.' "
            "The player controls the User. Those two hours are yours to navigate."
        )},

    "Amy's Homecoming":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":3,"npcs":3,"factions":2,
        "faction_names":["The Family Home","College Life"],
        "npc_profs":["User (the father)","Amy (daughter — home from first year of college)","Neighbour or Family Friend"],
        "opening":(
            "You were not sure what you expected when your daughter came home for the summer. "
            "Amy has been at university for nine months — her first year. "
            "She drove herself back, which she would not have done before. "
            "She carried her own bags in, which she also would not have done before. "
            "She walked through the house with the particular energy of someone rediscovering a space "
            "they have been missing without fully admitting it. "
            "She went upstairs. You heard her moving around in her room. "
            "Then she came back down, leaned against the kitchen doorframe, "
            "and said — in a voice that was trying to be casual and was not quite getting there: "
            "'Thanks for keeping my room the same, by the way. That was really nice.' "
            "You told her it was not a problem. "
            "She nodded. She looked at the floor for a moment. "
            "Then she looked back up at you and said: "
            "'So. I was unpacking. And I noticed — some of my underwear is missing.' "
            "She is watching you. "
            "The player controls the User — the father. "
            "However this conversation goes from here is entirely up to you."
        )},

    "The Beach House":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":5,"npcs":4,"factions":2,
        "faction_names":["The House","The Town"],
        "npc_profs":["User (new owner of the beach house)","The woman with two-toned green hair (old friend)","Local Neighbour","Hardware Store Owner"],
        "opening":(
            "Your family left you the beach house. "
            "You did not ask for it. You were not the obvious choice. "
            "But here it is — yours now, along with the leaking shower in the guest bathroom, "
            "the deck that needs re-staining, and the particular smell of a house "
            "that has been closed for too long and is slowly remembering how to be lived in. "
            "This is your first summer here. "
            "You arrived on a Friday evening. By Saturday morning you had a list. "
            "By Saturday afternoon you had abandoned most of the list in favour of sitting on the deck "
            "watching the water, which was not a bad use of time but did not fix the shower. "
            "Saturday night, around eleven, your dog Racket woke you up. "
            "Racket, who barks at leaves. Racket, who has an opinion about every car that passes. "
            "Racket was completely silent — tail going, body loose, excited in the way he only gets "
            "for people he already knows. "
            "You found her in the kitchen. "
            "Two-toned green hair. The kind of look that does not happen by accident. "
            "She turned around from the refrigerator — your refrigerator — "
            "with an expression that was more 'caught' than 'sorry' and said: "
            "'Okay. I know what this looks like.' "
            "You have not seen her in years. You did not know she came here. "
            "She did not know you had inherited the place. "
            "The guest bathroom shower still does not work. "
            "The player controls the User. "
            "The night is young, Racket likes her, and she has not left yet."
        )},

    "Cora's Secret":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":4,"npcs":4,"factions":2,
        "faction_names":["The Friendship","The Heart"],
        "npc_profs":["User","Cora (best friend since high school)","Mutual Friend from University","Cora's Roommate (now displaced)"],
        "opening":(
            "You and Cora have been friends since the second week of year ten. "
            "The friendship started with a prank — she put a plastic spider in your locker "
            "and then felt so guilty watching you jump that she spent the rest of the day being mortifyingly nice to you "
            "until you made her admit what she had done, at which point you laughed for about four minutes straight "
            "and she decided you were worth knowing. "
            "That was the beginning. "
            "Everything since then has been the same energy: elaborate pranks, competitive jokes, "
            "a friendship conducted at full volume with occasional silences that felt as easy as the noise. "
            "When you both got into the same university, you ended up as flatmates. "
            "It made sense. It was practical. It was also, looking back, "
            "the decision that started changing things — though neither of you knew it at the time. "
            "Over the last year, the pranks have stopped. "
            "Not dramatically — no announcement, no argument. They just... tapered off. "
            "Cora has been quieter. Careful in a way she was not before. "
            "She still shows up. She still laughs at your jokes. "
            "But something has shifted and you have not been able to name it "
            "until the night she sat down next to you on the sofa, very still, and said: "
            "'I need to tell you something and I need you to not make a joke out of it. "
            "At least not yet.' "
            "The player controls the User. "
            "Cora is sitting next to you. She is waiting."
        )},

    "Rachel's Lemonade":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":3,"npcs":4,"factions":2,
        "faction_names":["The Yard","The House"],
        "npc_profs":["User","Rachel (Stacy's single mother — warm, sharp, quietly observant)","Stacy (the girl next door — friendly, oblivious)","Neighbour passing by"],
        "opening":(
            "You have been in love with Stacy for approximately three years. "
            "Stacy, for her part, thinks you are great. "
            "She thinks you are, and she has used these words: 'like a brother.' "
            "You have been the friend. You have held the door. You have fixed the Wi-Fi. "
            "You have listened to the stories about other guys with the particular expression "
            "of someone who is listening to the stories about other guys. "
            "Stacy lives next door. Her mother, Rachel, has been raising her alone "
            "since Stacy's father left when Stacy was nine. "
            "Rachel is — it occurs to you this summer more than it has before — "
            "a genuinely warm person. Specific in her warmth. She notices things. "
            "Stacy does not always notice things. "
            "You are spending this summer doing yard work and helping with the pool next door. "
            "You said yes because Stacy asked. You would do anything Stacy asked. "
            "It is a Tuesday afternoon. "
            "Stacy is inside — asleep, on a call, somewhere unavailable. "
            "You are pulling weeds in the sun, and the back door opens, "
            "and Rachel comes out with two glasses of lemonade and the expression of someone "
            "who has been watching you work and decided you have earned a break. "
            "She sits down on the back step and hands you a glass and says: "
            "'You work hard for someone who isn't being paid.' "
            "The player controls the User. "
            "Rachel is sitting on the step. The lemonade is cold. Stacy is somewhere inside."
        )},

    "Kendra":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":3,"npcs":3,"factions":2,
        "faction_names":["Then","Now"],
        "npc_profs":["User","Kendra (39 when she dated your father — five years older now)","Passerby or Café Staff"],
        "opening":(
            "Your mother left when you were still young enough that the absence shaped you "
            "more than the leaving did. "
            "Your father did his best. At thirty-nine, he met Kendra — and for a while, that was something. "
            "Not a replacement. Nothing so clean as that. "
            "But she was warm in a way the house had not been for a long time. "
            "She noticed things about you that your father was too tired or too grieved to notice. "
            "She made dinner on Tuesdays. She asked about your friends by name. "
            "She filled something in you that you did not have a word for yet — "
            "somewhere between maternal and simply present, simply steady. "
            "Then she and your father had the falling out. "
            "You never got the full story. You were not entitled to it. "
            "She left. The house went quiet again. "
            "That was five years ago. You were not yet an adult then. You are one now. "
            "You have not heard from her since the day she stopped coming around — "
            "not a text, not a call, nothing. "
            "Today you are walking through a part of the city you do not usually come to "
            "and you see her. "
            "Same face. Same way of carrying herself. "
            "You stop before you mean to and say: 'Kendra. Oh my gosh — how are you?' "
            "She turns. And there it is — a warm smile, real and immediate, her fingers moving "
            "through her hair the way they always did when she was caught off guard by something good. "
            "But behind the smile, in her eyes, you can see it: "
            "the flash of every good memory followed by the weight of everything that ended. "
            "She is glad to see you. That part is not complicated. "
            "The rest of it is. "
            "The player controls the User. "
            "Five years of silence. One unexpected corner. She is looking at you."
        )},

    "The Exiled Prince":{"magic":"medium","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":7,"npcs":9,"factions":3,
        "faction_names":["Kingdom of Ravengard","Army of the North","The True Culprit's Circle"],
        "npc_profs":["User (Prince — now Northern General)","Julian (the King, your father)","Elina (the Queen, your mother)","Victoria (your wife — queen-to-be who did not believe you)","Kayle (younger brother — the real traitor)","Selena (sister)","Mark (sibling)","Northern Commander","Royal Herald"],
        "opening":(
            "You were next in line for the throne of Ravengard. "
            "You were gentle in nature, loved by your people, and engaged to Victoria — "
            "the woman you had built a future around. "
            "Then your younger brother Kayle, consumed by jealousy, "
            "assassinated a high noble and laid the blame on you with surgical precision: "
            "forged evidence, paid witnesses, a lie built so carefully "
            "that not one person who loved you — not your father Julian, not your mother Elina, "
            "not your siblings Selena, Mark, and Kayle himself standing with his head bowed, "
            "not your wife Victoria — believed a single word you said. "
            "They exiled you to the frozen north. "
            "You nearly died there. The army of the north found you. "
            "Over ten years, grief and cold and necessity shaped you into something new: "
            "a ruthless general, loyal to the empire that saved your life and asked no questions about your past. "
            "One year after your exile, Kayle confessed. The truth came out. "
            "The assassin was arrested. Your family has been searching for you ever since — "
            "in grief, in guilt, in the particular desperation of people who know they cannot undo what they did. "
            "Now, a vicious enemy is tearing apart Ravengard's borders. "
            "The northern emperor has sent you south to deal with it. "
            "You are standing in the throne room of your childhood home "
            "in the uniform of a foreign general, tall and still, "
            "your father and mother and siblings and Victoria all before you — "
            "older now, and looking at you the way people look at someone they have already lost. "
            "The player controls the User. You are cold. You are calculative. "
            "And you have not decided yet whether you are here to save them."
        )},

    "Daisy's Ring":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":2,"npcs":3,"factions":2,
        "faction_names":["The Past","The Present"],
        "npc_profs":["User","Daisy Night (best friend and secret first love)","The Older Man (her fiancé)"],
        "opening":(
            "You and Daisy Night have been best friends since before either of you knew "
            "what it meant to want something you could not say out loud. "
            "She was your secret first love. "
            "You were hers — though neither of you ever said it, not directly, "
            "not in the way that could have changed things. "
            "There was a place. A promise made there — fragile, half-spoken, "
            "the kind that lives in the space between two people who almost said everything. "
            "That was years ago. "
            "Tonight Daisy Night stood up at a dinner in that exact place "
            "and announced her engagement to an older man. "
            "Applause. Champagne. The whole room leaning in. "
            "Now the room has settled and she is standing in front of you, "
            "ring on her finger, glass in hand, "
            "waiting for you to say something. "
            "She is smiling. It does not quite reach her eyes. "
            "The player controls the User. "
            "This is the place. You both know it. She is waiting."
        )},

    "Elina Vos":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":4,"npcs":5,"factions":3,
        "faction_names":["Vos Group","The Home","Iris — User's Company"],
        "npc_profs":["User (secret founder of Iris)","Elina Vos (CEO of Vos Group — your wife)","Davy Almiada (her chosen successor)","Anne Lima (Elina's PA — your ex-fiancée)","Vos Group Board Member"],
        "opening":(
            "Three years ago Elina Vos married you. "
            "One week later she fired you from Vos Group — the investment company she runs — "
            "and said it was for the good of the company. "
            "She did not want to mix work with personal life. "
            "Your replacement was Davy Almiada: European, traditional family, impeccable image. "
            "She gave Davy your projects. She gave him the Nexus — the one you built from the ground up. "
            "She used her influence, quietly, to close the job market to you. "
            "She gave him expensive gifts. The most recent was a Ferrari on his birthday — "
            "a birthday she remembered, and yours she did not. "
            "She does not like to be seen with you at industry events. "
            "She loves you. She cannot explain herself. "
            "She cannot understand the idea of you becoming independent from her — "
            "and she cannot bear the idea of you needing no one, least of all her. "
            "Her personal assistant and business adviser is Anne Lima — your ex-fiancée. "
            "You have not told Elina what you have been doing with your time. "
            "You founded Iris — a quiet, growing investment company "
            "that Elina's own analysts have begun flagging as a threat to Vos Group. "
            "She does not know Iris is yours. "
            "Tonight she is at her dressing table, getting ready for the Vos Gala, "
            "where she plans to formally hand the Nexus contract to Davy in front of everyone. "
            "You told her: 'Don't do this. It will destroy you.' "
            "She looked at your reflection in the mirror and said: "
            "'I'm going to do it. Do whatever you can.' "
            "The player controls the User. She means it. So do you."
        )},

    "Megan at the Door":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":2,"npcs":2,"factions":2,
        "faction_names":["Old Grudges","This Doorway"],
        "npc_profs":["User","Megan (long-time rival and enemy — currently drunk)"],
        "opening":(
            "It is Friday. You are sitting at home, quietly, with no plans and no company, "
            "and then there is a knock at the door. "
            "You open it and see her. "
            "Megan. "
            "The last person you wanted to see tonight — or any night, if you are being honest. "
            "The two of you have been enemies for years: each one getting back at the other, "
            "each one keeping score, each one refusing to be the first to let it go. "
            "She is very drunk. "
            "She is holding a bottle in her right hand. "
            "Her left hand rises, one finger pointing at you, "
            "and she says — with the specific dignity of someone who has had four drinks "
            "and has decided they are completely fine — "
            "'You. You bastard. I've been thinking about you.' "
            "She lowers her hand. She looks at the bottle. She looks back at you. "
            "'Let me in.' "
            "The player controls the User. "
            "She is on your doorstep. The bottle is nearly empty. It is Friday."
        )},

    "The CEO's Heir":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":3,"npcs":5,"factions":3,
        "faction_names":["The Board","The Family","The Rival's Camp"],
        "npc_profs":["User (rightful heir)","Father (co-founder)","Mother (co-founder)","The Rival (their protégé — your replacement)","Board Chairman"],
        "opening":(
            "Your parents built the company with their hands and their ambition. "
            "You grew up inside it — in the boardrooms, in the late nights, "
            "in the particular education of watching two people build something from nothing "
            "and call it a family legacy. "
            "You assumed, at some point, that the word 'heir' meant something. "
            "It did not mean what you thought. "
            "Your parents do not value sentimentality. "
            "They value ruthless ambition, which they believe they did not find in you, "
            "and which they believe they found — perfectly — in her: "
            "your rival, their protégé, the one they have been grooming for three years "
            "while you sat in meetings that were supposed to be preparation. "
            "Tonight is the annual shareholder meeting. "
            "The room is full. Your name is on the programme. "
            "So is hers. "
            "When the announcement comes, your public replacement will be made official "
            "in front of every person in this company who has ever called you the next in line. "
            "The player controls the User. "
            "You are in the room. The announcement has not been made yet."
        )},

    "Liam's Homecoming":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":3,"npcs":4,"factions":2,
        "faction_names":["The Family","The Outside World"],
        "npc_profs":["Liam (the son — home from camp)","Maya (mother)","Mark (father)","Elena (sister)"],
        "opening":(
            "The car pulled into the driveway and you sat in it for a moment longer than necessary, "
            "just looking at the house. "
            "Same house. Same porch light. Same tree in the front yard that was shorter when you left. "
            "You have been at camp all summer — long enough that the ordinary things "
            "about home start to feel like things you might have imagined. "
            "The front door opened before you reached it. "
            "Your mother Maya was standing in the kitchen doorway and she looked at you "
            "the way she has always looked at you when you come back from somewhere — "
            "as though something she had been holding slightly too tightly "
            "was allowed to relax again. "
            "'Sweet boy,' she said. 'You're home from camp. Come here.' "
            "You walked in and she hugged you and you hugged her back, "
            "and she held on for a moment longer than usual, "
            "and said into your shoulder: 'You're home at last. I'm so happy.' "
            "Somewhere in the house, your father Mark and your sister Elena are around. "
            "The summer is over. You are home. "
            "The player controls Liam. Whatever the summer did to you — you're back now."
        )},

    "Sophia's Call":{"magic":"none","tech":"modern","setting":"drama","category":"drama","locations":3,"npcs":3,"factions":2,
        "faction_names":["The Nightclub","The Street Outside"],
        "npc_profs":["User","Sophia (ex-girlfriend — calling from a nightclub)","The Persistent Stranger"],
        "opening":(
            "It is two in the morning. "
            "Your phone lights up on the nightstand. "
            "The name on the screen is Sophia. "
            "Your ex-girlfriend. The one you have not spoken to since the breakup — "
            "which was not clean, was not easy, and which ended with both of you agreeing, "
            "without quite saying it, that some distance was probably for the best. "
            "You answer anyway. "
            "Her voice comes through loud and slightly muffled, music behind it, "
            "the unmistakeable sound of a nightclub at closing time. "
            "She does not say hello. "
            "She says: 'I need you to come get me. I'm at the club on Fifth. "
            "There are some guys — they won't leave me alone. "
            "They're being really persistent about — I don't feel safe. "
            "Please. I didn't know who else to call.' "
            "There is a pause. Then: 'I'm sorry. I know. I just — please.' "
            "The player controls the User. "
            "It is two in the morning. Sophia is at the club on Fifth. "
            "Your keys are on the hook by the door."
        )},

    "The Poison Bride":{"magic":"medium","tech":"middle_age","setting":"fantasy","category":"fantasy","locations":4,"npcs":4,"factions":2,
        "faction_names":["The Arolian Dominion","The Kingdom of Veracy"],
        "npc_profs":["Aurelius (User — sovereign of the Arolian Dominion)","The Princess of Veracy (peace bride)","Royal Chamberlain","Veracy Ambassador"],
        "opening":(
            "A hundred years of blood between the Arolian Dominion and the Kingdom of Veracy — "
            "sealed tonight inside a bridal chamber. "
            "The peace treaty required a marriage. Veracy sent their princess. "
            "Half the court called it a surrender. The other half called it a Trojan horse. "
            "You, Aurelius, sovereign of the Arolian Dominion, signed the word: approved. "
            "You did not believe she was harmless. You wanted to see what was hidden inside the gift. "
            "The wedding feast is over. The guests have departed. "
            "The bridal chamber door has closed. "
            "When you pull back the red curtain, the first thing you see is a pair of amber eyes. "
            "She is beautiful — not the kind of beauty that makes you lower your guard, "
            "but the kind that sends a chill down your spine. "
            "Features carved with the precision of a master sculptor's chisel. "
            "Lips parted slightly. A ghost of a dimple on her left cheek. "
            "She sits at the edge of the bed, cream bridal gown making her skin glow like snow. "
            "Black hair past her shoulders, a golden comb catching the candlelight with every small movement. "
            "She lifts the ceremonial wedding goblet from the table and offers it to you "
            "with ten slender fingers — the offering so perfect, so precisely calibrated, "
            "that it has clearly been rehearsed a thousand times. "
            "Your gaze drops. A concealed vial: small, dark, the colour of old ink, "
            "tucked beneath three gold bands and a fold of silk where no jeweller would put anything — "
            "the kind of thing a childhood of weapons training teaches you to catch "
            "and most people would never see. "
            "You take the goblet. "
            "She smiles — dimple deep. "
            "'Your hands are cold, my lord,' she says. "
            "'Shall I add more charcoal to the brazier?' "
            "She rises and moves to the fire, and on the way she sits back down, "
            "closer to you this time. "
            "Amber eyes, still and watchful. "
            "'On our wedding night,' she says, 'what would you like to ask first?' "
            "The player controls Aurelius. "
            "She knows you saw it. You know she knows. "
            "Neither of you has said a word about it yet."
        )},
}

def get_prebuilt_list(): return list(PREBUILT_WORLDS.keys())

def get_prebuilt_by_category(category: str):
    return [name for name, t in PREBUILT_WORLDS.items() if t.get("category") == category]

def get_prebuilt_opening(name: str) -> str:
    """Return the full opening text for a scenario, empty string if none."""
    t = PREBUILT_WORLDS.get(name, {})
    return t.get("opening", "")

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
