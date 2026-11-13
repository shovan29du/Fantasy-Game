"""In-app Help reference.

Reference tables are generated from the game's own data and constants so
they cannot drift from the rules the game actually applies. Only the
explanatory prose is written by hand.
"""
from __future__ import annotations

import math
import re

from shared_config import MEDIA_DIR
from backend.app.domain import dnd_weapons, multiverse, spells, weapons, worldscale
from backend.app.domain.characters import (
    ALIGNMENTS,
    CHARACTER_TAGS,
    DND_BACKGROUNDS,
    DND_RACES,
    MAGIC_TYPES,
    POWER_SYSTEMS,
    PROFESSIONS,
    QUIRKS_LIST,
    SKILLS_LIST,
)
from core import levelling, quest_system, relationship_engine, skill_tree_data, tactical_combat

STAT_LABELS = {
    "strength": "Strength", "dexterity": "Dexterity", "constitution": "Constitution",
    "intelligence": "Intelligence", "wisdom": "Wisdom", "charisma_stat": "Charisma",
    "speed": "Speed", "luck": "Luck",
}

STAT_MEANINGS = {
    "strength": "Physical power. Added to melee attack rolls and melee damage.",
    "dexterity": "Agility and reflexes. Added to attack rolls with finesse and ranged weapons.",
    "constitution": "Toughness. Raises maximum HP at every level.",
    "intelligence": "Reasoning and study. Raises maximum mana; casting ability for Wizards and Artificers.",
    "wisdom": "Awareness and willpower. Raises maximum mana; casting ability for Clerics, Druids, Rangers and Monks.",
    "charisma_stat": "Force of personality. Casting ability for Bards; gates most social skill-tree nodes.",
    "speed": "How quickly the character moves and reacts.",
    "luck": "Fortune. A general-purpose stat that quests and level-ups can raise.",
}

CLASS_BLURBS = {
    "Fighter": "Master of weapons and armour. Reliable damage and staying power, with a second attack each turn.",
    "Ranger": "Wilderness hunter and tracker who fights at range or with two weapons. Half-caster using Wisdom.",
    "Rogue": "Stealth, precision and trickery. Strikes hard from advantage and avoids a fair fight.",
    "Cleric": "Divine caster who heals and protects allies and smites enemies. Casts with Wisdom.",
    "Wizard": "Scholar of arcane magic with the widest spell choice. Fragile; casts with Intelligence.",
    "Bard": "Performer whose magic inspires allies and confounds foes. Casts with Charisma.",
    "Monk": "Martial artist who fights unarmed with speed and discipline. Gets a second attack each turn.",
    "Paladin": "Holy warrior in heavy armour who mixes weapon attacks with divine magic. Half-caster.",
    "Warlock": "Wields power granted by a pact with an otherworldly patron.",
    "Druid": "Caster who draws on nature: weather, beasts and plants. Casts with Wisdom.",
    "Barbarian": "Ferocious front-line warrior with the largest hit die (d12) and a second attack each turn.",
    "Sorcerer": "Innate caster whose magic comes from bloodline rather than study.",
    "Artificer": "Inventor who channels magic through crafted tools and devices. Casts with Intelligence.",
}

SCHOOL_BLURBS = {
    "Abjuration": "Protective magic: wards, shields and banishment.",
    "Conjuration": "Summons creatures or objects and moves things through space.",
    "Divination": "Reveals information: detecting, locating, foreseeing.",
    "Enchantment": "Influences minds: charming, commanding, calming.",
    "Evocation": "Raw energy: fire, lightning, force and healing light.",
    "Illusion": "Deceives the senses with false images and sounds.",
    "Transmutation": "Changes the properties of creatures and objects.",
    "Necromancy": "Manipulates life force and death.",
}

ALIGNMENT_BLURBS = {
    "Lawful Good": "Does what is right as society expects: honour, duty and compassion.",
    "Neutral Good": "Does the best a good person can, without bias for or against order.",
    "Chaotic Good": "Follows their own conscience to do good, with little regard for rules.",
    "Lawful Neutral": "Acts according to law, tradition or a personal code above all.",
    "True Neutral": "Avoids taking sides; acts on what seems best at the time.",
    "Chaotic Neutral": "Follows their whims and values personal freedom above everything.",
    "Lawful Evil": "Methodically takes what they want within a code of tradition or order.",
    "Neutral Evil": "Does whatever they can get away with, without compassion or qualms.",
    "Chaotic Evil": "Acts with arbitrary violence, driven by greed, hatred or bloodlust.",
}

WEAPON_PROPERTY_BLURBS = {
    "ammunition": "Needs ammunition to make a ranged attack.",
    "finesse": "Uses Dexterity instead of Strength for attack rolls.",
    "heavy": "Large and unwieldy; meant for strong wielders.",
    "light": "Small and quick; suited to fighting with a weapon in each hand.",
    "reach": "Attacks from 2 tiles away instead of 1.",
    "thrown": "Can be thrown to make a ranged attack.",
    "two_handed": "Needs both hands.",
    "versatile": "Can be used one- or two-handed.",
}

REWARD_BLURBS = {
    "gold": "Coins added to your purse; the amount scales with level.",
    "item": "A consumable or piece of gear added to your bag.",
    "stat_point": "+1 to one ability score.",
    "feat": "A feat from the Feats list.",
    "spell": "A new spell for your spellbook.",
    "skill": "A skill-tree ability.",
    "companion": "A companion who joins your story.",
    "ally": "An allied group or contact.",
    "title": "An honorific title.",
    "plot_item": "A story item that can drive later events.",
    "map_fragment": "A piece of a map pointing to somewhere new.",
}

QUEST_TYPE_BLURBS = {
    "story": "Main plot beats drawn from what has happened in your chat.",
    "daily": "Small routine tasks.",
    "bond": "Deepening a relationship with a companion or NPC.",
    "skill": "Practising or proving an ability.",
    "exploration": "Finding or reaching a place.",
    "combat": "Defeating a threat.",
    "delivery": "Carrying something to someone.",
    "investigation": "Uncovering information.",
    "random": "Any of the above, chosen at random.",
}

TAG_GROUPS = [
    ("Family and relationship roles",
     "Who the character is to you. Several of these set the character's starting trust.",
     ["Mom", "Daughter", "Wife", "Girlfriend", "Ex-Girlfriend", "Sister", "Aunt", "Cousin", "Grandmother",
      "Mother-in-law", "Boyfriend", "Husband", "Father", "Brother", "Son", "Uncle", "Grandfather", "Fiance(e)",
      "Crush", "Secret Admirer", "Childhood Friend", "Bestie", "Best Friend", "Rival", "Frenemy", "Partner",
      "Step-Mom", "Step-Dad", "Step-Sister", "Step-Brother"]),
    ("Social and work roles",
     "The character's position relative to you in everyday life.",
     ["Co-worker", "Boss", "Employee", "Neighbour", "Roommate", "Classmate", "Teacher", "Student", "Mentor",
      "Apprentice", "Landlord", "Client", "Maid", "Butler", "Nurse", "Servant", "Master", "Slave", "Royalty",
      "Commoner", "Prisoner", "Kidnapper"]),
    ("Personality archetypes",
     "Shorthand for how the character behaves.",
     ["Tsundere", "Yandere", "Kuudere", "Dandere", "Tomboy", "Bad Boy", "Bad Girl", "Good Girl", "Good Boy",
      "Nerd", "Jock", "Goth", "Punk", "Innocent", "Seductive", "Dangerous", "Protective", "Possessive",
      "Submissive", "Dominant", "Obsessive", "Stalker", "Cheater"]),
    ("Age group",
     "The character's stage of life. Sexual content involving anyone under 18 is never supported, "
     "whatever other tags are present.",
     ["Teen", "Young Adult", "Adult", "Mature", "Elder"]),
    ("Genre and setting",
     "The kind of story the character belongs in.",
     ["Office", "School", "Fantasy", "Sci-Fi", "Modern", "Historical", "Post-Apocalyptic", "Supernatural",
      "Mafia", "Crime", "Mystery", "Horror", "Romance", "Drama", "Comedy", "Slice of Life", "Isekai", "Harem",
      "Reverse Harem", "Magic", "Starfleet", "Jaffa"]),
    ("Story role",
     "The part the character plays in the plot.",
     ["Protagonist", "Antagonist", "Love Interest", "Villain", "Anti-Hero", "Companion"]),
    ("Creature type",
     "What kind of being the character is.",
     ["Alien", "Robot", "Angel", "Demon", "Vampire", "Werewolf", "Ghost", "Witch", "God/Goddess", "Neko",
      "Kitsune", "Alien GF"]),
    ("Themes",
     "Emotional threads the story is likely to follow.",
     ["Love", "Jealousy", "Betrayal", "Loyalty", "Revenge", "Redemption", "Adventure", "Survival", "Family"]),
    ("Romance tropes",
     "Common shapes for a romance plot.",
     ["Arranged Marriage", "Fake Dating", "Friends to Lovers", "Enemies to Lovers", "Second Chance", "Age Gap",
      "Forbidden", "Taboo", "Sugar Daddy", "Sugar Mommy"]),
    ("Adult content",
     "Mark a character or story as containing mature romantic or sexual themes. These apply to adult "
     "characters only.",
     ["NSFW", "Erotic", "Bondage", "Exhibitionist", "Voyeur", "MILF", "DILF", "Curvy", "Futa"]),
]

TAG_DEFINITIONS = {
    "Tsundere": "Cold or hostile on the surface, warm underneath.",
    "Yandere": "Affectionate to the point of dangerous obsession.",
    "Kuudere": "Calm, cool and seemingly emotionless, slowly showing they care.",
    "Dandere": "Quiet and shy, opening up once comfortable.",
    "Isekai": "Someone from our world is transported into another one.",
    "Harem": "One lead with several romantic interests.",
    "Reverse Harem": "A female lead with several male romantic interests.",
    "Slice of Life": "Everyday events rather than a big plot.",
    "Neko": "Part-cat person.",
    "Kitsune": "Fox spirit from Japanese folklore.",
    "Anti-Hero": "A lead who lacks conventional heroic qualities.",
    "Frenemy": "A friend who is also a rival.",
    "Starfleet": "Star Trek setting.",
    "Jaffa": "Stargate setting.",
    "Custom": "A free-text tag of your own.",
}


SECTION_ICONS = {
    "start": "🧭", "controls": "🎮", "rules": "📜", "combat": "⚔", "classes": "🛡", "races": "👥", "feats": "⭐",
    "spells": "✨", "skilltree": "🌳", "character": "🎭", "tags": "🏷", "equipment": "🗡", "monsters": "👹",
    "quests": "🗺", "relationships": "❤", "worlds": "🌍", "limits": "⚠",
}

SECTION_PICTURES = {
    "start": "an adventurer standing before a glowing portal at dawn, wide fantasy landscape",
    "controls": "an ornate fantasy game table with a map, tokens and dice seen from above",
    "rules": "an open ancient rulebook with dice and a quill on a wooden desk, candlelight",
    "combat": "a party of adventurers fighting goblins on a stone battlefield, dynamic action",
    "classes": "a line-up of fantasy heroes: fighter, wizard, rogue, cleric, ranger, heroic poses",
    "races": "a gathering of fantasy peoples: human, elf, dwarf, dragonborn and tiefling in a tavern",
    "feats": "a hero performing an impossible acrobatic sword strike, glowing aura",
    "spells": "a wizard casting a swirling arcane spell with glowing runes",
    "skilltree": "a glowing constellation shaped like a branching tree of abilities in the night sky",
    "character": "a character sheet, portrait sketches and coloured inks on an artist's desk",
    "tags": "a wall of colourful hanging paper labels and ribbons in a fantasy market",
    "equipment": "a medieval armoury wall with swords, axes, bows and shields",
    "monsters": "a shadowy cave with glowing eyes of lurking monsters, torchlight",
    "quests": "a quest board covered in parchment notices in a village square",
    "relationships": "two adventurers sharing a campfire under the stars, warm light",
    "worlds": "several planets and floating islands linked by glowing portals in space",
    "limits": "a calm stone gate with a protective glowing ward, soft light",
}
PICTURE_STYLE = "fantasy rpg illustration, painterly, detailed, atmospheric lighting, no text, no watermark"
HELP_MEDIA = MEDIA_DIR / "help"


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_") or "x"


def _stat(key: str) -> str:
    return STAT_LABELS.get(key, key.replace("_stat", "").replace("_", " ").title())


def _mod(score: int) -> int:
    return (score - 10) // 2


def _signed(n: int) -> str:
    return f"+{n}" if n >= 0 else f"−{abs(n)}"


def _dice(spec) -> tuple[int, int, float] | None:
    """(minimum, maximum, average) of a dice expression such as '2d6+3'."""
    low = high = 0
    try:
        for term in str(spec).replace(" ", "").lower().split("+"):
            if not term:
                continue
            if "d" in term:
                n, m = term.split("d")
                n = int(n or 1)
                low += n
                high += n * int(m)
            else:
                low += int(term)
                high += int(term)
    except ValueError:
        return None
    return (low, high, (low + high) / 2) if high else None


def _dice_text(spec) -> str:
    d = _dice(spec)
    return f"{d[0]}–{d[1]}, average {d[2]:g}" if d else ""


def _hit_chance(bonus: int, ac: int) -> tuple[int, int]:
    """(lowest d20 roll that hits, percent chance). A 1 always misses and a 20 always hits."""
    need = min(20, max(2, ac - bonus))
    return need, (21 - need) * 5


def _combat_hp(hit_die: int, level: int, con_mod: int) -> int:
    return max(1, (hit_die + con_mod) + max(0, level - 1) * (hit_die // 2 + 1 + con_mod))


def _entry(name: str, summary: str = "", *, stats: dict | None = None, example: str = "",
           links: list | None = None, icon: str = "", picture: str = "", **fields) -> dict:
    """One Help entry. `links` are (label, target) pairs where target is a
    section id, 'section/Entry name', or 'view:<name>'. `picture` is the
    prompt used to pre-generate the entry's illustration."""
    return {
        "name": name, "summary": summary,
        "fields": {k: v for k, v in fields.items() if v not in ("", None, [], {})},
        "stats": {k: v for k, v in (stats or {}).items() if v not in ("", None)},
        "example": example,
        "links": list(links or []),
        "icon": icon,
        "picture": picture,
    }


def _join(values) -> str:
    return ", ".join(str(v) for v in values if v not in ("", None))


def _getting_started() -> dict:
    return {"id": "start", "title": "Getting started", "intro": "How a game is set up and where things are.", "entries": [
        _entry("What you need", "Worldweaver runs on your computer. The story is written by a local AI model served by "
               "LM Studio on port 1234. Without it the map, character sheet, combat and quests still work, but chat "
               "replies show an error with a Retry button.",
               example="If chat shows “LM Studio isn't running”, start LM Studio's local server, load a model, "
                       "then press Retry on the message.",
               links=[("Controls and options", "controls"), ("Open Settings", "view:settings")]),
        _entry("Starting a story", "Play → New Game, pick a scenario, then create your character (name is the only "
               "required field) or choose a saved one. The game opens in the same tab.",
               example="Play → New Game → pick “Pirate Seas” → type the name “Mira Vale”, occupation “Ranger” → "
                       "Start Adventure.",
               links=[("Classes", "classes"), ("Races", "races"), ("Open Play", "view:play")]),
        _entry("Each story has its own character", "Creating a character for a new story always makes a separate "
               "character, even if the name matches one you already have. Quests, memories and relationships stay "
               "with the story they came from. To carry a character into a new story on purpose, pick them under "
               "“Or continue with a saved character”.",
               example="You play “Aria” in a pirate story, then start a zombie story and type “Aria” again: "
                       "the second Aria starts at level 1 with no quests and nobody remembers the first.",
               links=[("Quests belong to a character", "quests/Quests belong to a character"),
                      ("Memory", "relationships/Memory")]),
        _entry("The game screen", "Top bar: menu, Back, Close and Save. Party bar: your character, "
               "companions and active quests. Left: the map and the action bar. Centre: the chat with the "
               "storyteller. Right: Character, Inventory, Spellbook, Skill Tree, Skills, Progress, Orgs and World panels.",
               links=[("Top bar", "controls/Top bar"), ("Action bar", "controls/Action bar"), ("Map", "controls/Map")]),
        _entry("Saving and loading", "Save game stores the current story under a name. Play → Load Saved Game "
               "reopens one. Your current story is also resumed automatically when you return to Play.",
               example="Before a risky fight, press Save game and name it “Before the troll”. If it goes badly, "
                       "load that save.",
               links=[("Open Play", "view:play")]),
        _entry("Other areas", "Characters: build detailed characters. World: create and edit worlds. Knowledge: "
               "lorebook entries and documents the storyteller can draw on. Media: image, voice and animation tools. "
               "Explore: search for community characters. Settings: model, voice and app options.",
               links=[("Open Characters", "view:characters"), ("Open World", "view:worlds"),
                      ("Open Knowledge", "view:knowledge"), ("Open Media", "view:media"),
                      ("Open Explore", "view:explore"), ("Open Settings", "view:settings")]),
    ]}


def _controls() -> dict:
    return {"id": "controls", "title": "Controls and options", "intro": "Buttons, keys and chat commands.", "entries": [
        _entry("Top bar", "", **{
            "☰": "Show or hide the main menu while playing.",
            "‹ Back": "Return to scenario selection without ending the current story.",
            "✕ Close": "Return to the Play hub. “Back to game” resumes.",
            "Save game": "Save or load this story.",
        }, example="To check a spell mid-fight: press ?, search the spell, then press Play in the menu to return.",
           links=[("Saving and loading", "start/Saving and loading")]),
        _entry("Keyboard", "", **{
            "W A S D / arrow keys": "Walk on the map.",
            "1 2 3 4": "Switch map scale: Local, Country, Continent, Universe.",
            "Esc": "Close the open dialog, map preview or menu.",
        }, example="Press 4 to see the Universe map, click a world, then press 1 to return to the Local map."),
        _entry("Map", "Click the map to move and click a location to explore it. Local shows places in the current "
               "town, Country shows regions, Continent shows nations, Universe shows the worlds you can travel to. "
               "The portal travels between worlds. +30m advances the clock; Generate adds a new location.",
               example="Click “Old Mill” on the Local map: the scene picture loads and a panel lists the people, "
                       "loot and quests found there.",
               links=[("Travelling between worlds", "worlds/Travelling between worlds"),
                      ("Time, weather and threat", "worlds/Time, weather and threat")]),
        _entry("Action bar", "", **{
            "Engage Enemies": "Start a tactical combat encounter.",
            "Fire Bolt": "Practice attack that grants a little XP.",
            "Guard / Aegis / Blink": "Readied stances, shown for flavour outside combat.",
            "Inspect / Loot": "Examine the area or search it for an item.",
            "Short Rest": "1 hour. Restores a quarter of maximum HP and mana for the whole party.",
            "Long Rest": "8 hours. Restores all HP and mana for the whole party.",
        }, example="At 12 of 40 HP, a Short Rest brings you to 22 and moves the clock on an hour.",
           links=[("Combat", "combat"), ("Resting", "rules/Resting"), ("Experience and levels", "rules/Experience and levels")]),
        _entry("Chat box", "", **{
            "Send": "Send your action or speech to the storyteller.",
            "✦ Options": "Suggests several things you could do next.",
            "🎤": "Dictate a message (Chrome or Edge).",
            "📎": "Attach a file for the storyteller to read.",
            "Voice": "Read replies aloud.",
            "⬇ Zip": "Download the chat as text, JSON and HTML.",
        }, example="Type “I search the captain's desk for the missing ledger” and press Send. Stuck? Press "
                   "✦ Options for five suggestions.",
           links=[("How replies are formatted", "controls/How replies are formatted")]),
        _entry("Chat commands", "", **{
            "/help": "Show the short command list in chat.",
            "/place Name, Terrain, Description": "Add a location to the map. Terrain: Forest, City, Ruins, "
                                                 "Underground, Ocean, Mountains, Plains, Desert, Swamp.",
            "*add location: Name, local|country|continent|universe*": "Add a location at a chosen map scale.",
        }, example="/place Old Mill, Forest, A ruined watermill where smugglers meet",
           links=[("Map", "controls/Map")]),
        _entry("Message actions", "Hover a chat message for its buttons.", **{
            "Copy / Paste to input / Select": "Reuse the text.",
            "Edit": "Change the message.",
            "Delete": "Remove this message.",
            "Rewind": "Delete this message and everything after it.",
            "Regenerate": "Ask the storyteller for a different reply.",
            "Progress story forward": "Continue the story from here.",
            "Generate media": "Make an image from the message.",
            "Save to memory": "Pin the message as a fact for this story.",
        }, example="The storyteller forgets the innkeeper's name: find the message that introduced her and "
                   "press Save to memory.",
           links=[("Memory", "relationships/Memory")]),
        _entry("How replies are formatted", "“Name: text” is dialogue. **Bold text** is action or narration.",
               example="**The door creaks open.** Captain Hayate: “You are late.”"),
        _entry("Party", "Click a party member to speak as them; “Narrator” returns to the storyteller. "
               "“Recruit companion” adds a saved character (up to 6 in the party) and can delete saved characters.",
               example="Click your companion Kael's card and type “I'll take first watch” — the line is spoken "
                       "as Kael.",
               links=[("Relationships", "relationships")]),
    ]}


def _core_rules() -> dict:
    max_level = 20
    xp_rows = {f"Level {lv}": f"{levelling.xp_for_level(lv):,} XP" for lv in range(1, max_level + 1)}
    prof_rows = {}
    for lv in range(1, max_level + 1):
        prof_rows.setdefault(f"+{levelling.proficiency_bonus(lv)}", []).append(lv)
    prof_rows = {bonus: f"Levels {lvs[0]}–{lvs[-1]}" for bonus, lvs in prof_rows.items()}
    asi = sorted(levelling.ASI_LEVELS)
    return {"id": "rules", "title": "Core rules", "intro": "The game uses D&D 5e-style rules, simplified in places.", "entries": [
        _entry("Ability scores", f"Eight scores, normally starting at 10 and capped at {levelling.STAT_MAX}.",
               stats={"Scores": len(levelling.STAT_NAMES), "Typical start": 10, "Maximum": levelling.STAT_MAX},
               example="A Fighter with Strength 16 adds +3 to melee attack and damage rolls; with Constitution 14 "
                       "they gain 2 extra HP every level.",
               links=[("Ability modifier", "rules/Ability modifier"), ("Races", "races"), ("Attack rolls", "combat/Attack rolls")],
               **{_stat(k): STAT_MEANINGS.get(k, "") for k in levelling.STAT_NAMES}),
        _entry("Ability modifier", "(score − 10) ÷ 2, rounded down. A score of 10–11 gives +0, 14–15 gives +2, "
               "18–19 gives +4. Modifiers, not raw scores, are added to rolls.",
               stats={f"Score {sc}": _signed(_mod(sc)) for sc in (8, 10, 12, 14, 16, 18, 20)},
               example=f"Dexterity 15: (15 − 10) ÷ 2 = 2.5, rounded down to {_signed(_mod(15))}. "
                       f"Strength 9: (9 − 10) ÷ 2 = −0.5, rounded down to {_signed(_mod(9))}.",
               links=[("Ability scores", "rules/Ability scores")]),
        _entry("Proficiency bonus", "Added to attack rolls. It grows with level.",
               stats={f"Level {lv}": _signed(levelling.proficiency_bonus(lv)) for lv in (1, 5, 9, 13, 17)},
               example=f"At level 5 your proficiency bonus is {_signed(levelling.proficiency_bonus(5))}, so with "
                       f"Strength 16 you attack at d20 {_signed(3 + levelling.proficiency_bonus(5))}.",
               links=[("Attack rolls", "combat/Attack rolls")], **prof_rows),
        _entry("Hit points and mana", "Outside combat: max HP = 20 + 8 per level + Constitution modifier per level; "
               "max mana = 10 + 4 per level + the better of your Intelligence or Wisdom modifier per level. "
               "In tactical combat HP follows the class hit die: full die + CON modifier at level 1, then half the "
               "die + 1 + CON modifier for each further level.",
               stats={"HP per level": "8 + CON modifier", "Mana per level": "4 + INT or WIS modifier"},
               example=f"Level 3, Constitution 14, Intelligence 16: max HP = 20 + 3×8 + 3×2 = {20 + 24 + 6}; "
                       f"max mana = 10 + 3×4 + 3×3 = {10 + 12 + 9}. In combat as a Fighter (d10) the same "
                       f"character has {_combat_hp(10, 3, 2)} HP.",
               links=[("Classes", "classes"), ("Resting", "rules/Resting"), ("Falling to 0 HP", "combat/Falling to 0 HP")]),
        _entry("Experience and levels", "XP comes from completing quests and practice actions. Reaching a threshold "
               "raises your level immediately and queues a level-up choice.",
               stats={f"Level {lv}": f"{levelling.xp_for_level(lv):,} XP" for lv in (2, 5, 10, 20)},
               example=f"A Story quest gives {quest_system._QXP['story']} XP and a Combat quest "
                       f"{quest_system._QXP['combat']}. Together that is {quest_system._QXP['story'] + quest_system._QXP['combat']} "
                       f"XP — exactly enough for level 2 ({levelling.xp_for_level(2)} XP).",
               links=[("Quests and rewards", "quests"), ("Levelling up", "rules/Levelling up")], **xp_rows),
        _entry("Levelling up", "When a level-up is waiting, the Level Up button on the Character panel glows. "
               "Each level offers:", **{
                   "Hit points": "Between 1 and your hit die, plus your Constitution modifier.",
                   "Ability scores": f"+1 to one score. At levels {_join(asi)} you get an Ability Score Improvement: "
                                     "+2 to one score, +1 to two scores, or a feat instead.",
                   "Spells": "Casters are offered new spells every 2 levels, everyone else every 4. The highest "
                             "spell level offered is half your level, rounded up.",
                   "Skill tree": "Up to four abilities you now qualify for.",
                   "Story abilities": "Abilities written by the storyteller for your character and story.",
                   "Class": "At levels 5, 10, 15 and 20 you may move up to the next class tier.",
               }, stats={"Ability Score Improvements": f"Levels {_join(asi)}", "Class change": "Levels 5, 10, 15, 20"},
               example=f"Reaching level 4 as a Wizard (d{levelling.get_hit_die('wizard')}, Constitution 12): gain "
                       f"{1 + 1}–{levelling.get_hit_die('wizard') + 1} HP, choose +2 Intelligence or a feat, pick a "
                       "new spell and a skill-tree ability.",
               links=[("Feats", "feats"), ("Spells", "spells"), ("Skill tree", "skilltree"), ("Classes", "classes")]),
        _entry("Resting", "Short Rest takes 1 hour and restores 25% of maximum HP and mana. Long Rest takes 8 hours "
               "and restores everything. Both apply to the whole party and advance the world clock.",
               stats={"Short Rest": "1 hour · 25%", "Long Rest": "8 hours · 100%"},
               example="With 40 max HP and 10 left: a Short Rest restores 10 (to 20); a Long Rest restores all 40.",
               links=[("Action bar", "controls/Action bar"), ("Hit points and mana", "rules/Hit points and mana")]),
    ]}


def _combat() -> dict:
    grid = tactical_combat.GRID_SIZE
    move = tactical_combat.MOVE_SPEED
    slot_rows = {f"Caster level {lv}": _join(f"{n}× level {s}" for s, n in tactical_combat._spell_slots_for("wizard", lv).items())
                 for lv in range(1, 11)}
    tiers = tactical_combat._MONSTERS_BY_TIER
    danger_rows = {f"Danger {i * 2}–{i * 2 + 1}" if i < len(tiers) - 1 else f"Danger {i * 2}+": _join(pool)
                   for i, pool in enumerate(tiers)}
    return {"id": "combat", "title": "Combat", "intro": f"Engage Enemies starts a turn-based fight on a {grid}×{grid} grid.", "entries": [
        _entry("Turn order", "Everyone rolls initiative (d20 + modifier) and acts from highest to lowest. "
               "Two allies fight beside you and act on their own; enemies are controlled by the game.",
               stats={"Grid": f"{grid}×{grid}", "Allies": len(tactical_combat.ALLY_DEFS), "Enemies": "2–6"},
               example="You roll 14 + 2, a goblin rolls 9 + 2: you act first (16 beats 11).",
               links=[("Your turn", "combat/Your turn"), ("Monsters", "monsters")]),
        _entry("Your turn", "You have movement, one Action, and a Reaction. They can be used in any order and you "
               "end the turn with End Turn.", **{
                   "Movement": f"Up to {move} tiles. You can move, act, then move again.",
                   "Attack": "Click an enemy in range. Uses your Action.",
                   "Cast a spell": "Pick a spell from the list, then a target. Uses your Action and a spell slot "
                                   "(cantrips are free).",
                   "Dash": f"Uses your Action to gain {move} more tiles of movement this turn.",
                   "Disengage": "Uses your Action; your movement provokes no opportunity attacks this turn.",
                   "Dodge": "Uses your Action; attacks against you have disadvantage until your next turn.",
                   "Play / Pause": "Lets the game play your turns automatically until you pause it.",
               }, stats={"Movement": f"{move} tiles", "Actions": 1, "Reactions": 1},
               example=f"Move 3 tiles to reach an orc, attack it (Action), then move your other {move - 3} tiles "
                       "away — though leaving its reach lets it strike back.",
               links=[("Attack rolls", "combat/Attack rolls"), ("Opportunity attacks", "combat/Opportunity attacks"),
                      ("Spell slots", "combat/Spell slots")]),
        _entry("Attack rolls", "Roll d20 + ability modifier + proficiency bonus. The attack hits if the total "
               "equals or beats the target's Armour Class (AC). Strength is used for melee, Dexterity for finesse "
               "and ranged weapons. A natural 20 always hits and is a critical hit (weapon dice are doubled). "
               "A natural 1 always misses.",
               stats={"Roll": "d20 + ability mod + proficiency", "Hit": "total ≥ target AC", "Critical": "natural 20"},
               example=f"Level 1 with Strength 16: d20 + 3 + 2. Against a goblin (AC 15) you hit on a roll of "
                       f"{_hit_chance(5, 15)[0]} or higher — a {_hit_chance(5, 15)[1]}% chance.",
               links=[("Ability modifier", "rules/Ability modifier"), ("Proficiency bonus", "rules/Proficiency bonus"),
                      ("Armour Class", "combat/Armour Class"), ("Weapons and equipment", "equipment")]),
        _entry("Armour Class", "Your AC is 10 + Dexterity modifier + the bonus of your best equipped armour.",
               stats={"Base": 10, "Unarmoured, DEX 14": 12},
               example="Dexterity 14 (+2) wearing armour with +4 AC: 10 + 2 + 4 = AC 16.",
               links=[("Attack rolls", "combat/Attack rolls")]),
        _entry("Damage", "Weapon dice + ability modifier. A unit at 0 HP is out of the fight.",
               example=f"A longsword (1d8) with Strength 16 deals 1d8 + 3: {_dice_text('1d8+3')}. On a critical hit "
                       f"the dice double to 2d8 + 3: {_dice_text('2d8+3')}.",
               links=[("Weapons and equipment", "equipment"), ("Falling to 0 HP", "combat/Falling to 0 HP")]),
        _entry("Advantage and disadvantage", "Advantage rolls two d20 and keeps the higher; disadvantage keeps "
               "the lower.",
               example="Attacking a Dodging enemy you roll 17 and 6 and must use the 6.",
               links=[("Your turn", "combat/Your turn")]),
        _entry("Range and cover", "Melee weapons reach 1 tile, reach weapons 2, ranged weapons 4. Higher-tier "
               "weapons without a D&D entry reach 3 tiles (tiers 4–6) or 5 (tier 7+). Ranged attacks need a clear "
               "line; obstacles block them and block movement.",
               stats={"Melee": "1 tile", "Reach": "2 tiles", "Ranged": "4 tiles"},
               example="A shortbow can hit a target 4 tiles away, but not one standing behind a wall tile.",
               links=[("Weapon properties", "equipment/Weapon properties")]),
        _entry("Opportunity attacks", "Leaving a melee enemy's reach lets it attack you once per round as a "
               "reaction, unless you Disengaged. The same applies to enemies leaving yours.",
               example="You stand next to a wolf and walk away: it bites as you leave. Had you used Disengage "
                       "first, it could not.",
               links=[("Your turn", "combat/Your turn")]),
        _entry("Extra attack", "Fighters, Paladins, Rangers, Barbarians and Monks may attack twice with one Action.",
               example="A Fighter attacks an orc and kills it, then uses the second attack on the goblin beside it.",
               links=[("Classes", "classes")]),
        _entry("Power attack", "With Great Weapon Master (melee) or Sharpshooter (ranged) you may take −5 to hit "
               "for +10 damage.",
               stats={"To hit": "−5", "Damage": "+10"},
               example=f"Normally +5 to hit for 2d6 + 3 ({_dice_text('2d6+3')}). As a power attack: +0 to hit for "
                       f"2d6 + 13 ({_dice_text('2d6+13')}). Worth it against low-AC targets.",
               links=[("Great Weapon Master", "feats/Great Weapon Master"), ("Sharpshooter", "feats/Sharpshooter")]),
        _entry("Falling to 0 HP", "Your character falls unconscious and makes a death saving throw each turn: "
               "10 or more is a success, less is a failure, a 1 counts as two failures, and a 20 puts you back on "
               "1 HP. Three successes stabilise you; three failures mean death.",
               stats={"Success": "10 or more", "Stabilise": "3 successes", "Death": "3 failures"},
               example="You roll 12 (success), 4 (failure), 1 (two failures): that is three failures, and the "
                       "character dies. A healing spell from an ally would have brought you back up.",
               links=[("Spells", "spells")]),
        _entry("Spell slots", "Full casters use this table; Paladins and Rangers count as half their level. "
               "Classes that are not casters have no slots.",
               example="A level 3 Wizard has four level-1 slots and two level-2 slots. Casting Magic Missile "
                       "(level 1) uses one level-1 slot; Fire Bolt (a cantrip) uses none.",
               links=[("Spells", "spells"), ("Classes", "classes")], **slot_rows),
        _entry("Winning and losing", "You win when every enemy is down and lose when your whole side is. "
               "Result & End closes the encounter.",
               links=[("Falling to 0 HP", "combat/Falling to 0 HP")]),
        _entry("Enemies by danger", "The world's Danger rating decides how many enemies appear (2 to 6) and which "
               "kinds.",
               example="In a world with Danger 4 you face 4 enemies drawn from: " + _join(tiers[min(len(tiers) - 1, 2)]) + ".",
               links=[("Monsters", "monsters"), ("Danger rating", "worlds/Danger rating")], **danger_rows),
    ]}


def _classes() -> dict:
    tiers = levelling.PROFESSION_TIERS
    levels = sorted(tiers)
    base_level = levels[1]
    entries = []
    for i, name in enumerate(tiers[base_level]):
        path = [tiers[lv][i] for lv in levels[1:] if i < len(tiers[lv])]
        key = name.lower()
        die = levelling.get_hit_die(name)
        caster = levelling.is_caster(key)
        casting = spells.CASTING_ABILITY_BY_PROFESSION.get(name)
        extra = tactical_combat._has_extra_attack(name)
        links = [("Levelling up", "rules/Levelling up"), ("Hit points and mana", "rules/Hit points and mana")]
        if caster or casting:
            links += [("Spells", "spells"), ("Spell slots", "combat/Spell slots")]
        if extra:
            links.append(("Extra attack", "combat/Extra attack"))
        links.append(("Build a character", "view:characters"))
        entries.append(_entry(name, CLASS_BLURBS.get(name, ""),
            stats={"Hit die": f"d{die}", **{f"HP at level {lv}": _combat_hp(die, lv, 2) for lv in (1, 5, 10, 20)}},
            example=f"A level 5 {name} with Constitution 14 has {_combat_hp(die, 5, 2)} HP in combat "
                    f"(d{die} + 2 at level 1, then {die // 2 + 1} + 2 per level) and a proficiency bonus of "
                    f"{_signed(levelling.proficiency_bonus(5))}.",
            links=links,
            picture=f"a fantasy {name} adventurer, full body character concept art, {CLASS_BLURBS.get(name, '')}",
            **{
                "Spellcaster": "Yes — offered spells every 2 levels" if caster else "No — offered spells every 4 levels",
                "Casting ability": _stat(casting) if casting else "",
                "Two attacks per Action": "Yes" if extra else "",
                "Class path": " → ".join(f"{p} (level {lv})" for p, lv in zip(path, levels[1:])),
            }))
    entries.append(_entry("Starting titles", "Before level 5 a character holds a beginner title and uses a d6 hit die.",
                          stats={"Hit die": "d6", "HP at level 1": _combat_hp(6, 1, 2)},
                          example=f"A level 3 Adventurer with Constitution 14 has {_combat_hp(6, 3, 2)} HP in combat.",
                          links=[("Changing class", "classes/Changing class")],
                          **{"Titles": _join(tiers[levels[0]])}))
    entries.append(_entry("Changing class", "At levels 5, 10, 15 and 20 the level-up screen offers the classes of "
                          "that tier. Each tier is a stronger form of the one before it.",
                          example=" → ".join(tiers[lv][0] for lv in levels) + ".",
                          links=[("Levelling up", "rules/Levelling up")]))
    entries.append(_entry("Occupations", "The character builder also offers everyday and fantasy occupations. "
                          "They describe who the character is; one whose name matches a class above uses that "
                          "class's hit die.",
                          example="A “Doctor” uses the default d6 hit die; a “Fighter” uses d10.",
                          links=[("Build a character", "view:characters")],
                          **{"Occupations": _join(PROFESSIONS)}))
    return {"id": "classes", "title": "Classes", "intro": "A class sets your hit die, whether you cast spells, and your upgrade path.", "entries": entries}


_ABILITY_ABBR = {"STR": "Strength", "DEX": "Dexterity", "CON": "Constitution", "INT": "Intelligence",
                 "WIS": "Wisdom", "CHA": "Charisma", "SPD": "Speed", "LCK": "Luck"}


def _race_example(name: str, bonuses: dict) -> str:
    for key, value in bonuses.items():
        try:
            amount = int(str(value).replace("+", ""))
        except ValueError:
            continue
        if key == "All":
            return f"A {name} who would have 10 in every ability score starts with {10 + amount} in each."
        ability = _ABILITY_ABBR.get(key, key)
        return (f"A {name} with a base {ability} of 13 starts at {13 + amount} "
                f"(modifier {_signed(_mod(13 + amount))} instead of {_signed(_mod(13))}).")
    return f"Choose {name} as the race on the character builder to apply its bonuses and features."


def _races() -> dict:
    entries = []
    for name, race in DND_RACES.items():
        bonuses = race.get("stat_bonuses") or {}
        entries.append(_entry(name, race.get("lore", ""),
            stats={**{_ABILITY_ABBR.get(k, k): v for k, v in bonuses.items()},
                   "Speed": f"{race['speed']} ft" if race.get("speed") else "", "Size": race.get("size", "")},
            example=_race_example(name, bonuses),
            links=[("Ability scores", "rules/Ability scores"), ("Classes", "classes"), ("Build a character", "view:characters")],
            picture=f"portrait of a {name} character, {race.get('lore', '')}",
            **{
                "Features": _join(race.get("features", [])),
                "Traits": _join(race.get("traits", [])),
                "Languages": _join(race.get("languages", [])),
                "Lifespan": race.get("age_range", ""),
                "Height": race.get("height", "") if isinstance(race.get("height"), str) else "",
            }))
    return {"id": "races", "title": "Races", "intro": f"{len(entries)} playable races. Each gives ability bonuses and innate features.", "entries": entries}


FEAT_EXAMPLES = {
    "Great Weapon Master": "With a greatsword you may attack at −5 to hit for +10 damage: 2d6 + 13 instead of 2d6 + 3.",
    "Sharpshooter": "With a longbow you may attack at −5 to hit for +10 damage: 1d8 + 13 instead of 1d8 + 3.",
    "Lucky": "You roll a 1 on an attack. Once per fight Lucky lets you roll again and use the new result.",
}


def _feats() -> dict:
    asi = sorted(levelling.ASI_LEVELS)
    entries = []
    for name, feat in levelling.DND_FEATS.items():
        prereq = feat.get("prereq")
        if prereq:
            stat, _, value = str(prereq).partition(">=")
            prereq = f"{_stat(stat)} {value} or higher"
        bonus = feat.get("bonus") or {}
        example = FEAT_EXAMPLES.get(name)
        if not example:
            gain = _join(f"{_stat(k)} rises from 10 to {10 + v}" for k, v in bonus.items())
            example = (f"At level {asi[0]} you take {name} instead of +2 to an ability score"
                       + (f": {gain}." if gain else "."))
        links = [("Levelling up", "rules/Levelling up")]
        if name in ("Great Weapon Master", "Sharpshooter"):
            links.append(("Power attack", "combat/Power attack"))
        if name in tactical_combat.COMBAT_FEATS:
            links.append(("Combat", "combat"))
        entries.append(_entry(name, feat.get("desc", ""),
            stats={"Category": str(feat.get("category", "")).title(),
                   **{_stat(k): _signed(v) for k, v in bonus.items()}},
            example=example, links=links,
            picture=f"a fantasy hero showing the talent “{name}”: {feat.get('desc', '')}",
            **{
                "Requires": prereq or "",
                "In tactical combat": "Has a direct effect in fights" if name in tactical_combat.COMBAT_FEATS else "",
            }))
    return {"id": "feats", "title": "Feats", "intro": "Special talents. You can take one in place of an Ability Score "
            f"Improvement at levels {_join(asi)}, or earn one from a quest.", "entries": entries}


def _spell_example(name: str, spell: dict) -> str:
    effect = spell.get("effect_type")
    if effect == "attack":
        dmg = _dice_text(spell.get("damage"))
        if spell.get("auto_hit"):
            return f"{name} never misses: it deals {spell.get('damage')} {spell.get('damage_type', '')} damage ({dmg})."
        need, pct = _hit_chance(5, 15)
        return (f"A level 1 caster with a +3 casting modifier rolls d20 + 3 + 2 to hit. Against AC 15 that hits "
                f"on {need}+ ({pct}%), for {spell.get('damage')} {spell.get('damage_type', '')} damage ({dmg}).")
    if effect == "save":
        return (f"A level 1 caster with a +3 casting modifier sets DC 8 + 2 + 3 = 13. The target rolls a "
                f"{_stat(spell.get('save_ability', 'dexterity'))} save: on a failure it takes "
                f"{spell.get('damage')} ({_dice_text(spell.get('damage'))}), on a success half.")
    if effect == "heal":
        return f"Cast on a wounded ally it restores {spell.get('heal')} HP ({_dice_text(spell.get('heal'))}) and wakes them if unconscious."
    if spell.get("ac_bonus"):
        return f"A caster with AC 12 has AC {12 + int(spell['ac_bonus'])} while {name} lasts ({spell.get('duration', '')})."
    return f"Cast {name} with your Action; its effect lasts: {spell.get('duration', 'as described')}."


def _spells() -> dict:
    class_names = set(levelling.PROFESSION_TIERS[sorted(levelling.PROFESSION_TIERS)[1]])
    entries = [_entry("Spell levels", "Level 0 spells are cantrips and cost nothing to cast. Level 1 and higher "
                      "spells use a spell slot of that level in combat. You learn spells at level-up and from quests.",
                      stats={"Cantrips": sum(1 for v in spells.SPELLS.values() if v.get("level", 0) == 0),
                             "Levelled spells": sum(1 for v in spells.SPELLS.values() if v.get("level", 0) > 0)},
                      example="Fire Bolt (cantrip) can be cast every turn. Fireball (level 3) needs a level-3 slot, "
                              "which a Wizard first has at level 5.",
                      links=[("Spell slots", "combat/Spell slots"), ("Levelling up", "rules/Levelling up")]),
               _entry("Casting ability", "The ability that powers a class's spells. Its modifier is added to spell "
                      "attack rolls and sets the difficulty of saving throws against your spells.",
                      stats={"Spell attack": "d20 + casting mod + proficiency", "Save DC": "8 + proficiency + casting mod"},
                      example="A level 5 Wizard with Intelligence 18 (+4): spell attacks roll d20 + 7 and enemies "
                              "save against DC 15.",
                      links=[("Ability modifier", "rules/Ability modifier"), ("Classes", "classes")],
                      **{_stat(ability): _join(k for k, v in spells.CASTING_ABILITY_BY_PROFESSION.items() if v == ability)
                         for ability in dict.fromkeys(spells.CASTING_ABILITY_BY_PROFESSION.values())}),
               _entry("Schools of magic", "Every spell belongs to a school describing the kind of magic it is.",
                      stats={s: sum(1 for v in spells.SPELLS.values() if v.get("school") == s) for s in spells.SPELL_SCHOOLS},
                      example="Fireball is Evocation (raw energy); Shield is Abjuration (protection).",
                      **{s: SCHOOL_BLURBS.get(s, "") for s in spells.SPELL_SCHOOLS})]
    for name, spell in sorted(spells.SPELLS.items(), key=lambda kv: (kv[1].get("level", 0), kv[0])):
        level = spell.get("level", 0)
        links = [("Schools of magic", "spells/Schools of magic"), ("Spell slots", "combat/Spell slots")]
        links += [(c, f"classes/{c}") for c in spell.get("classes", []) if c in class_names]
        dmg = _dice(spell.get("damage")) if spell.get("damage") else None
        heal = _dice(spell.get("heal")) if spell.get("heal") else None
        entries.append(_entry(name, spell.get("description", ""),
            stats={
                "Level": "Cantrip" if level == 0 else level,
                "Damage": f"{spell['damage']} (avg {dmg[2]:g})" if dmg else "",
                "Healing": f"{spell['heal']} (avg {heal[2]:g})" if heal else "",
                "AC": f"+{spell['ac_bonus']}" if spell.get("ac_bonus") else "",
                "Range": spell.get("range", ""),
            },
            example=_spell_example(name, spell), links=links,
            picture=f"magic spell effect “{name}”: {spell.get('description', '')}, glowing magical energy",
            **{
                "School": spell.get("school", ""),
                "Classes": _join(spell.get("classes", [])),
                "Casting time": spell.get("casting_time", ""),
                "Duration": spell.get("duration", ""),
                "Components": spell.get("components", ""),
                "Damage type": str(spell.get("damage_type", "")).title(),
                "Saving throw": _stat(spell["save_ability"]) if spell.get("save_ability") else "",
                "Always hits": "Yes" if spell.get("auto_hit") else "",
            }))
    return {"id": "spells", "title": "Spells", "intro": f"{len(spells.SPELLS)} spells across {len(spells.SPELL_SCHOOLS)} schools.", "entries": entries}


def _skill_path(node: dict, nodes: dict) -> list[str]:
    """Names from a root ability down to `node`, following the first prerequisite each time."""
    path, seen = [node["name"]], {node["id"]}
    while node.get("parents"):
        parent = nodes.get(node["parents"][0])
        if not parent or parent["id"] in seen:
            break
        path.append(parent["name"])
        seen.add(parent["id"])
        node = parent
    return path[::-1]


def _skill_tree() -> dict:
    nodes = skill_tree_data.ALL_NODES
    names = [n["name"] for n in nodes.values()]
    unique = {n for n in names if names.count(n) == 1}
    entries = [_entry("Unlocking abilities", "An ability can be unlocked when you meet its level and ability-score "
                      "requirements and already have every ability it builds on. Unlock them from the Skill Tree "
                      "panel or as a level-up choice.",
                      stats={"Abilities": len(nodes), "Branches": len(skill_tree_data.CATEGORIES), "Tiers": 4},
                      example="Power Strike needs Basic Attack first. With Basic Attack unlocked, the right level "
                              "and enough Strength, its node lights up and can be taken.",
                      links=[("Levelling up", "rules/Levelling up"), ("Ability scores", "rules/Ability scores")])]
    for category in skill_tree_data.CATEGORIES:
        label = skill_tree_data.CATEGORY_LABELS.get(category, category.title())
        for node in sorted((n for n in nodes.values() if n["category"] == category), key=lambda n: (n["tier"], n["level_req"], n["name"])):
            path = _skill_path(node, nodes)
            reqs = _join(f"{_stat(k)} {v}" for k, v in node.get("attr_req", {}).items())
            example = ("Unlock path: " + " → ".join(path) + "." if len(path) > 1
                       else f"A starting ability: available from level {node['level_req']}" + (f" with {reqs}." if reqs else "."))
            parents = [nodes[p]["name"] for p in node.get("parents", []) if p in nodes]
            entries.append(_entry(node["name"], node.get("desc", ""),
                stats={"Branch": label, "Tier": node["tier"], "Level": node["level_req"]},
                example=example,
                links=[("Unlocking abilities", "skilltree/Unlocking abilities")] + [(p, f"skilltree/{p}") for p in parents if p in unique],
                icon=node.get("icon", ""),
                **{"Requires": reqs, "Builds on": _join(parents)}))
    return {"id": "skilltree", "title": "Skill tree", "intro": f"{len(nodes)} abilities in {len(skill_tree_data.CATEGORIES)} branches and 4 tiers.", "entries": entries}


def _character_options() -> dict:
    build = [("Build a character", "view:characters")]
    return {"id": "character", "title": "Character options", "intro": "Choices on the character builder.", "entries": [
        _entry("Alignment", "A character's moral outlook, on two axes: Lawful–Chaotic and Good–Evil.",
               stats={"Alignments": len(ALIGNMENTS)},
               example="A paladin who keeps every oath is Lawful Good; a thief who robs the rich to feed the poor "
                       "is Chaotic Good.", links=build,
               **{a: ALIGNMENT_BLURBS.get(a, "") for a in ALIGNMENTS}),
        _entry("Backgrounds", "What the character did before the story began. It colours how the storyteller "
               "writes them.", stats={"Backgrounds": len(DND_BACKGROUNDS)},
               example=f"An {DND_BACKGROUNDS[0]} is likely to be recognised and helped at a temple." if DND_BACKGROUNDS else "",
               links=build, **{"Backgrounds": _join(DND_BACKGROUNDS)}),
        _entry("Skills", "Things the character is practised at. The storyteller takes them into account when "
               "describing what you attempt.", stats={"Skills": len(SKILLS_LIST)},
               example="With Stealth you might write “I slip past the guards along the rooftops” and expect to "
                       "be good at it.", links=build + [("Skill tree", "skilltree")],
               **{"Skills": _join(SKILLS_LIST)}),
        _entry("Quirks", "Small habits that make a character distinctive.", stats={"Quirks": len(QUIRKS_LIST)},
               example=f"A character with “{QUIRKS_LIST[0]}” will do so in the storyteller's descriptions." if QUIRKS_LIST else "",
               links=build, **{"Quirks": _join(QUIRKS_LIST)}),
        _entry("Magic types", "The flavour of magic a character uses.", stats={"Types": len(MAGIC_TYPES)},
               example="A Wizard with Fire and Illusion magic is described hurling flames and conjuring false images.",
               links=build + [("Spells", "spells")], **{"Types": _join(MAGIC_TYPES)}),
        _entry("Power systems", "Where a character's power comes from, for settings that are not plain D&D.",
               stats={"Systems": len(POWER_SYSTEMS)},
               example="In a ninja setting choose Chakra; in a martial-arts epic choose Qi / Ki.",
               links=build, **{"Systems": _join(POWER_SYSTEMS)}),
        _entry("Origins", "The kind of world the character comes from.", stats={"Origins": len(multiverse.CHARACTER_ORIGINS)},
               example="A “Modern Earth” character dropped into a fantasy world will not know what a mana potion is.",
               links=build + [("Worlds and the multiverse", "worlds")], **{"Origins": _join(multiverse.CHARACTER_ORIGINS)}),
        _entry("Power tier", "A rough ceiling on how powerful a character is.",
               stats={"Tiers": f"0–{multiverse.POWER_TIERS[-1]['tier']}"},
               example="A standard adventurer is tier 2 (Heroic); a dragon or archmage is tier 4 (Legendary).",
               links=build + [("Power rating", "worlds/Power rating")],
               **{f"Tier {t['tier']} — {t['name']}": t["scope"] for t in multiverse.POWER_TIERS}),
        _entry("Values", "Eight sliders from 0 to 100 describing what the character believes in.",
               stats={"Sliders": len(multiverse.VALUES_AXES), "Range": "0–100"},
               example="Mercy 90 means the character spares a beaten enemy; Mercy 10 means they finish the job.",
               links=build, **{k.replace("_", " ").title(): v for k, v in multiverse.VALUES_AXES.items()}),
    ]}


def _tags() -> dict:
    trust = relationship_engine.TAG_TRUST_MAP
    sample = [t for t in ("Rival", "Tsundere") if t in trust]
    entries = [_entry("What tags do", "Tags label a character's role, personality, genre and themes. They are used "
                      "to organise and search characters, and some set how much a character trusts you at the "
                      "start. Tags never override the content limits: no sexual content involving anyone under 18.",
                      stats={"Tags": len(CHARACTER_TAGS), "Tags that set trust": sum(1 for t in CHARACTER_TAGS if t in trust)},
                      example=(f"A character tagged {_join(sample)} and Fantasy starts at trust "
                               f"{int(sum(trust[t] for t in sample) / len(sample))}: the average of "
                               + " and ".join(f"{t} {trust[t]}" for t in sample) + " (Fantasy sets no trust).") if sample else "",
                      links=[("Trust", "relationships/Trust"), ("Content limits", "limits"), ("Build a character", "view:characters")])]
    placed: set[str] = set()
    for title, blurb, names in TAG_GROUPS:
        present = [t for t in names if t in CHARACTER_TAGS]
        placed.update(present)
        fields = {t: TAG_DEFINITIONS[t] for t in present if t in TAG_DEFINITIONS}
        fields["Tags"] = _join(present)
        starting = {t: trust[t] for t in present if t in trust}
        if starting:
            fields["Starting trust (0–100)"] = _join(f"{t} {v}" for t, v in starting.items())
        example = ""
        if starting:
            top = max(starting, key=starting.get)
            low = min(starting, key=starting.get)
            example = f"“{top}” starts a character at trust {starting[top]}; “{low}” at {starting[low]}."
        elif present:
            example = f"Tag a character “{present[0]}” to file them under {title.lower()} and find them by that tag."
        entries.append(_entry(title, blurb, stats={"Tags": len(present)}, example=example,
                              links=[("What tags do", "tags/What tags do")] + ([("Trust", "relationships/Trust")] if starting else []),
                              **fields))
    rest = [t for t in CHARACTER_TAGS if t not in placed]
    if rest:
        fields = {t: TAG_DEFINITIONS[t] for t in rest if t in TAG_DEFINITIONS}
        fields["Tags"] = _join(rest)
        entries.append(_entry("Other", "Tags that fit no group above.", stats={"Tags": len(rest)},
                              links=[("What tags do", "tags/What tags do")], **fields))
    return {"id": "tags", "title": "Tags", "intro": f"{len(CHARACTER_TAGS)} tags in groups.", "entries": entries}


def _equipment() -> dict:
    props = sorted({p for w in dnd_weapons.DND_WEAPONS.values() for p in w.get("properties", [])})
    entries = [_entry("Weapon properties", "Keywords on a weapon that change how it is used.",
                      stats={"Properties": len(props)},
                      example="A rapier is finesse: a Rogue with Dexterity 18 and Strength 8 attacks with +4, not −1.",
                      links=[("Attack rolls", "combat/Attack rolls"), ("Range and cover", "combat/Range and cover")],
                      **{p.replace("_", "-"): WEAPON_PROPERTY_BLURBS.get(p, "") for p in props}),
               _entry("Equipping", "Equip items from the Inventory panel. An equipped weapon sets your attack "
                      "damage and range in combat; equipped armour raises your Armour Class.",
                      example="Equip a longbow and your attacks reach 4 tiles and use Dexterity.",
                      links=[("Armour Class", "combat/Armour Class"), ("Damage", "combat/Damage")])]
    for name, weapon in dnd_weapons.DND_WEAPONS.items():
        properties = weapon.get("properties", [])
        dex = "finesse" in properties or "Ranged" in weapon.get("category", "")
        ability = "Dexterity" if dex else "Strength"
        reach = tactical_combat._weapon_range_for(name, weapon.get("tier"))
        dmg = _dice(weapon.get("damage"))
        tier = weapon.get("tier")
        links = [("Weapon properties", "equipment/Weapon properties"), ("Attack rolls", "combat/Attack rolls")]
        if tier is not None and tier in weapons.TIER_BY_NUMBER:
            links.append((f"Weapon tier {tier}", f"equipment/Weapon tier {tier} — {weapons.TIER_BY_NUMBER[tier]['era']}"))
        entries.append(_entry(name, f"{weapon.get('category', 'Weapon')} dealing {weapon.get('damage_type', '')} damage.",
            stats={"Damage": f"{weapon.get('damage', '')} (avg {dmg[2]:g})" if dmg else weapon.get("damage", ""),
                   "Reach": f"{reach} tile{'s' if reach != 1 else ''}", "Uses": ability, "Tier": tier},
            example=(f"With {ability} 16 at level 1 you attack at d20 + 5 and deal {weapon.get('damage')} + 3 "
                     f"({_dice_text(str(weapon.get('damage')) + '+3')}).") if dmg else "",
            links=links,
            picture=f"a {name}, medieval fantasy weapon, single item illustration on a dark background",
            **{"Category": weapon.get("category", ""), "Properties": _join(p.replace("_", "-") for p in properties)}))
    for tier in weapons.WEAPON_TIERS:
        examples = tier.get("examples", [])
        entries.append(_entry(f"Weapon tier {tier['tier']} — {tier['era']}", "A world's Weapon rating is the "
                              "highest tier normally available there.",
                              stats={"Tier": tier["tier"], "Era": tier["era"]},
                              example=(f"In a world with Weapon rating {tier['tier']} you can expect to find: "
                                       f"{_join(examples)}.") if examples else "",
                              links=[("Weapon rating", "worlds/Weapon rating")],
                              **{
                                  "Examples": _join(examples),
                                  "Strengths": _join(tier.get("properties", [])),
                                  "Limitations": _join(tier.get("limitations", [])),
                              }))
    return {"id": "equipment", "title": "Weapons and equipment", "intro": f"{len(dnd_weapons.DND_WEAPONS)} D&D weapons and {len(weapons.WEAPON_TIERS)} technology tiers.", "entries": entries}


def _monsters() -> dict:
    tiers = tactical_combat._MONSTERS_BY_TIER
    entries = []
    for name, m in sorted(tactical_combat.DND_MONSTERS.items(), key=lambda kv: (kv[1].get("cr", 0), kv[0])):
        need, pct = _hit_chance(5, m.get("ac", 10))
        dmg = _dice(m.get("damage"))
        dangers = [f"{i * 2}–{i * 2 + 1}" if i < len(tiers) - 1 else f"{i * 2}+" for i, pool in enumerate(tiers) if name in pool]
        entries.append(_entry(name, f"Appears at Danger {_join(dangers)}." if dangers else "",
            stats={"CR": m.get("cr", ""), "HP": m.get("hp", ""), "AC": m.get("ac", ""),
                   "Damage": f"{m.get('damage')} (avg {dmg[2]:g})" if dmg else m.get("damage", ""),
                   "Move": f"{m['speed']} tiles" if m.get("speed") else ""},
            example=(f"A level 1 character attacking at +5 hits its AC {m.get('ac')} on a roll of {need}+ ({pct}%). "
                     + (f"Dealing 1d8 + 3 (average 7.5) per hit, it falls in about {max(1, math.ceil(m['hp'] / 7.5))} "
                        f"hit{'s' if math.ceil(m['hp'] / 7.5) > 1 else ''}."
                        if m.get("hp") else "")),
            links=[("Attack rolls", "combat/Attack rolls"), ("Enemies by danger", "combat/Enemies by danger")],
            picture=f"a {name}, dungeons and dragons style monster, menacing creature illustration",
            **{"Weapon": m.get("weapon", "")}))
    return {"id": "monsters", "title": "Monsters", "intro": "Enemies that can appear in tactical combat.", "entries": entries}


def _quests() -> dict:
    level2 = levelling.xp_for_level(2)
    entries = [
        _entry("Getting quests", "Generate (in the quest bar) asks the storyteller for a quest based on your recent "
               "chat. A story quest is also offered automatically every 8 replies while you have fewer than 4. "
               "Locations can offer quests of their own. If the storyteller is unavailable a simple templated "
               "quest is created instead.",
               stats={"Automatic story quest": "every 8 replies", "Up to": "4 active"},
               example="After the storyteller describes a sealed letter marked in blood, Generate may offer "
                       "“The Sealed Letter: deliver it before dawn”.",
               links=[("Map", "controls/Map")]),
        _entry("Completing quests", "Mark a quest complete from the quest bar. You receive its XP and one reward "
               "drawn from that quest type's list. Abandoning a quest gives nothing.",
               example=f"Completing a Combat quest gives {quest_system._QXP['combat']} XP plus one of: "
                       f"{_join(r.replace('_', ' ') for r in quest_system._REWARD_POOL['combat'])}.",
               links=[("Reward types", "quests/Reward types"), ("Experience and levels", "rules/Experience and levels")]),
        _entry("Quests belong to a character", "Each character has their own quests, even when two characters "
               "share a name.",
               example="Two characters named “Aria” in different stories each see only their own quests.",
               links=[("Each story has its own character", "start/Each story has its own character")]),
    ]
    for qtype in quest_system.QUEST_TYPES:
        xp = quest_system._QXP.get(qtype, 40)
        entries.append(_entry(f"{qtype.title()} quest", QUEST_TYPE_BLURBS.get(qtype, ""),
            stats={"XP": xp, "Rewards": len(quest_system._REWARD_POOL.get(qtype, []))},
            example=f"{math.ceil(level2 / xp)} {qtype} quest{'s' if math.ceil(level2 / xp) != 1 else ''} "
                    f"({math.ceil(level2 / xp) * xp} XP) take a new character to level 2, which needs {level2} XP.",
            links=[("Reward types", "quests/Reward types"), ("Experience and levels", "rules/Experience and levels")],
            **{"Possible rewards": _join(r.replace("_", " ") for r in quest_system._REWARD_POOL.get(qtype, []))}))
    entries.append(_entry("Reward types", "What a completed quest can give you besides XP.",
                          stats={"Kinds": len(REWARD_BLURBS)},
                          example="A Story quest might grant a feat; a Daily quest some gold.",
                          links=[("Feats", "feats"), ("Spells", "spells"), ("Skill tree", "skilltree")],
                          **{k.replace("_", " ").title(): v for k, v in REWARD_BLURBS.items()}))
    return {"id": "quests", "title": "Quests and rewards", "intro": "How quests are created and what they pay.", "entries": entries}


def _relationships() -> dict:
    after_gifts = min(100, 50 + 16)
    return {"id": "relationships", "title": "Relationships", "intro": "How characters come to trust you.", "entries": [
        _entry("Trust", "Each character you talk to has a trust score from 0 to 100, starting at 50 unless their "
               "tags say otherwise. It is tracked separately in each story.",
               stats={"Range": "0–100", "Default": 50},
               example=f"From 50, two gifts (+8 each) raise trust to {after_gifts}: "
                       f"{relationship_engine._bond_from_trust(after_gifts).replace('_', ' ')}, mood "
                       f"{relationship_engine._mood_from_trust(after_gifts)}.",
               links=[("What changes trust", "relationships/What changes trust"), ("Bond", "relationships/Bond"),
                      ("Tags", "tags")]),
        _entry("What changes trust", "Each exchange nudges trust up or down.",
               stats={"Biggest gain": "Gift +8", "Biggest loss": "Betrayal −15"},
               example="Insulting a friend at 40 trust drops them to 34: still “pleasant”, but no longer a friend "
                       "(friend starts at 35).",
               links=[("Trust", "relationships/Trust")], **{
            "Friendly message": "+3", "Hostile message": "−4", "Help": "+5", "Gift": "+8", "Flirt": "+4",
            "Quest completed": "+5", "Insult": "−6", "Attack": "−10", "Betrayal": "−15",
        }),
        _entry("Bond", "The relationship label, set by trust.",
               stats={"Levels": 6},
               example=f"At trust 76 a character is your {relationship_engine._bond_from_trust(76).replace('_', ' ')}.",
               links=[("Trust", "relationships/Trust")], **{
            "Stranger": "below 15", "Acquaintance": "15–34", "Friend": "35–54", "Close friend": "55–74",
            "Trusted ally": "75–89", "Soulbound": "90 or more",
        }),
        _entry("Mood", "How the character feels towards you, set by trust.",
               stats={"Levels": 6},
               example=f"At trust 18 a character is {relationship_engine._mood_from_trust(18)}; at 62 they are "
                       f"{relationship_engine._mood_from_trust(62)}.",
               links=[("Trust", "relationships/Trust")], **{
            "Hostile": "below 10", "Annoyed": "10–19", "Neutral": "20–39", "Pleasant": "40–59",
            "Happy": "60–79", "Elated": "80 or more",
        }),
        _entry("Memory", "The storyteller remembers what happens in a story and brings it back later. Memories "
               "stay inside their story. “Save to memory” on a chat message pins it for that story.",
               example="Pin “The innkeeper Marta owes you a favour”; weeks of story later, Marta still remembers.",
               links=[("Message actions", "controls/Message actions"),
                      ("Each story has its own character", "start/Each story has its own character")]),
    ]}


def _worlds() -> dict:
    entries = [_entry("World ratings", "Every world is rated 0–10 on eight axes. They tell the storyteller what "
                      "is possible there and decide things like the weapons and enemies you meet.",
                      stats={"Axes": len(worldscale.WORLD_AXES), "Scale": "0–10"},
                      example="“Magic 7 · Tech 2 · Weapon 5” describes a high-magic world with medieval technology.",
                      links=[("Open World", "view:worlds")])]
    extra_links = {"weapon": [("Weapons and equipment", "equipment")], "power": [("Power tier", "character/Power tier")],
                   "danger": [("Enemies by danger", "combat/Enemies by danger")], "magic": [("Spells", "spells")]}
    for axis, description in worldscale.WORLD_AXES.items():
        labels = worldscale.AXIS_LEVEL_LABELS.get(axis, [])
        mid = min(len(labels) - 1, 5) if labels else 0
        entries.append(_entry(f"{axis.title()} rating", description,
                              stats={"0": labels[0], "10": labels[-1]} if labels else {},
                              example=f"A world with {axis.title()} {mid} is “{labels[mid]}”." if labels else "",
                              links=[("World ratings", "worlds/World ratings")] + extra_links.get(axis, []),
                              **{str(i): label for i, label in enumerate(labels)}))
    entries.append(_entry("Reality types", "How a world relates to others in the multiverse.",
                          stats={"Types": len(multiverse.REALITY_TYPES)},
                          example="In a Mirror Universe your loyal companion from the Prime Reality may be your enemy.",
                          links=[("Travelling between worlds", "worlds/Travelling between worlds")],
                          **dict(multiverse.REALITY_TYPES)))
    entries.append(_entry("Travelling between worlds", "Use the portal on the map or the Universe tab. "
                          "A world's ratings apply as soon as you arrive.",
                          example="Step through the portal from a Magic 8 world into a Magic 0 one and your "
                                  "spells stop being part of how that world works.",
                          links=[("Map", "controls/Map"), ("World ratings", "worlds/World ratings")]))
    entries.append(_entry("Time, weather and threat", "The bar under the map shows the time of day, day count, "
                          "weather and threat level. Resting and +30m advance the clock.",
                          example="A Long Rest at 22:00 on Day 1 ends at 06:00 on Day 2.",
                          links=[("Resting", "rules/Resting")]))
    return {"id": "worlds", "title": "Worlds and the multiverse", "intro": "World ratings and travel.", "entries": entries}


def _content_limits() -> dict:
    return {"id": "limits", "title": "Content limits", "intro": "What the storyteller will not write.", "entries": [
        _entry("Always enforced", "The storyteller narrates action, conflict, romance and dark themes as the story "
               "calls for them. It does not write scenes that sexualise minors, or non-consensual scenarios "
               "involving real, identifiable living people. No tag, scenario or setting changes this.",
               example="A horror story with violence and a villain's cruelty is fine. A sexual scene involving a "
                       "character under 18 is refused, whatever tags the character has.",
               links=[("Tags", "tags")]),
    ]}


def _sections() -> list[dict]:
    return [
        _getting_started(), _controls(), _core_rules(), _combat(), _classes(), _races(), _feats(), _spells(),
        _skill_tree(), _character_options(), _tags(), _equipment(), _monsters(), _quests(), _relationships(),
        _worlds(), _content_limits(),
    ]


def _picture_url(section_id: str, entry_id: str) -> str:
    path = HELP_MEDIA / section_id / f"{entry_id}.jpg"
    return f"/media/help/{section_id}/{entry_id}.jpg" if path.is_file() else ""


def picture_specs() -> list[dict]:
    """Every Help picture to pre-generate: {section, id, prompt, path}. Topic
    banners come first, then entries in topic order."""
    sections = _sections()
    specs = [{"section": "sections", "id": s["id"], "prompt": f"{SECTION_PICTURES[s['id']]}, {PICTURE_STYLE}",
              "path": HELP_MEDIA / "sections" / f"{s['id']}.jpg"} for s in sections if s["id"] in SECTION_PICTURES]
    for section in sections:
        for entry in section["entries"]:
            if entry["picture"]:
                eid = _slug(entry["name"])
                specs.append({"section": section["id"], "id": eid, "prompt": f"{entry['picture']}, {PICTURE_STYLE}",
                              "path": HELP_MEDIA / section["id"] / f"{eid}.jpg"})
    return specs


def find_picture_spec(section_id: str, entry_id: str) -> dict | None:
    """The pre-defined picture for one entry (or section banner), or None."""
    return next((sp for sp in picture_specs() if sp["section"] == section_id and sp["id"] == entry_id), None)


def build_help() -> list[dict]:
    """Every Help section, in display order, ready for the Help view."""
    sections = _sections()
    known = {s["id"]: {e["name"] for e in s["entries"]} for s in sections}
    for section in sections:
        section["icon"] = SECTION_ICONS.get(section["id"], "")
        section["image"] = _picture_url("sections", section["id"])
        section["can_picture"] = section["id"] in SECTION_PICTURES
        for entry in section["entries"]:
            entry["id"] = _slug(entry["name"])
            entry["icon"] = entry["icon"] or section["icon"]
            entry["image"] = _picture_url(section["id"], entry["id"])
            entry["can_picture"] = bool(entry["picture"])
            del entry["picture"]
            links = []
            for label, target in entry["links"]:
                if target.startswith("view:"):
                    links.append({"label": label, "view": target[5:]})
                    continue
                sec, _, name = target.partition("/")
                if sec in known and (not name or name in known[sec]):
                    links.append({"label": label, "section": sec, "entry": _slug(name) if name else ""})
            entry["links"] = links
    return sections
