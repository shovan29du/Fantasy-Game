"""In-app Help reference.

Reference tables are generated from the game's own data and constants so
they cannot drift from the rules the game actually applies. Only the
explanatory prose is written by hand.
"""
from __future__ import annotations

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


def _stat(key: str) -> str:
    return STAT_LABELS.get(key, key.replace("_stat", "").replace("_", " ").title())


def _entry(name: str, summary: str = "", **fields) -> dict:
    """One Help entry. Empty fields are dropped."""
    return {"name": name, "summary": summary, "fields": {k: v for k, v in fields.items() if v not in ("", None, [], {})}}


def _join(values) -> str:
    return ", ".join(str(v) for v in values if v not in ("", None))


def _getting_started() -> dict:
    return {"id": "start", "title": "Getting started", "intro": "How a game is set up and where things are.", "entries": [
        _entry("What you need", "Worldweaver runs on your computer. The story is written by a local AI model served by "
               "LM Studio on port 1234. Without it the map, character sheet, combat and quests still work, but chat "
               "replies show an error with a Retry button."),
        _entry("Starting a story", "Play → New Game, pick a scenario, then create your character (name is the only "
               "required field) or choose a saved one. The game opens in the same tab."),
        _entry("Each story has its own character", "Creating a character for a new story always makes a separate "
               "character, even if the name matches one you already have. Quests, memories and relationships stay "
               "with the story they came from. To carry a character into a new story on purpose, pick them under "
               "“Or continue with a saved character”."),
        _entry("The game screen", "Top bar: menu, Back, Close and Save. Party bar: your character, "
               "companions and active quests. Left: the map and the action bar. Centre: the chat with the "
               "storyteller. Right: Character, Inventory, Spellbook, Skill Tree, Skills, Progress, Orgs and World panels."),
        _entry("Saving and loading", "Save game stores the current story under a name. Play → Load Saved Game "
               "reopens one. Your current story is also resumed automatically when you return to Play."),
        _entry("Other areas", "Characters: build detailed characters. World: create and edit worlds. Knowledge: "
               "lorebook entries and documents the storyteller can draw on. Media: image, voice and animation tools. "
               "Explore: search for community characters. Settings: model, voice and app options."),
    ]}


def _controls() -> dict:
    return {"id": "controls", "title": "Controls and options", "intro": "Buttons, keys and chat commands.", "entries": [
        _entry("Top bar", "", **{
            "☰": "Show or hide the main menu while playing.",
            "‹ Back": "Return to scenario selection without ending the current story.",
            "✕ Close": "Return to the Play hub. “Back to game” resumes.",
            "Save game": "Save or load this story.",
        }),
        _entry("Keyboard", "", **{
            "W A S D / arrow keys": "Walk on the map.",
            "1 2 3 4": "Switch map scale: Local, Country, Continent, Universe.",
            "Esc": "Close the open dialog, map preview or menu.",
        }),
        _entry("Map", "Click the map to move and click a location to explore it. Local shows places in the current "
               "town, Country shows regions, Continent shows nations, Universe shows the worlds you can travel to. "
               "The portal travels between worlds. +30m advances the clock; Generate adds a new location."),
        _entry("Action bar", "", **{
            "Engage Enemies": "Start a tactical combat encounter.",
            "Fire Bolt": "Practice attack that grants a little XP.",
            "Guard / Aegis / Blink": "Readied stances, shown for flavour outside combat.",
            "Inspect / Loot": "Examine the area or search it for an item.",
            "Short Rest": "1 hour. Restores a quarter of maximum HP and mana for the whole party.",
            "Long Rest": "8 hours. Restores all HP and mana for the whole party.",
        }),
        _entry("Chat box", "", **{
            "Send": "Send your action or speech to the storyteller.",
            "✦ Options": "Suggests several things you could do next.",
            "🎤": "Dictate a message (Chrome or Edge).",
            "📎": "Attach a file for the storyteller to read.",
            "Voice": "Read replies aloud.",
            "⬇ Zip": "Download the chat as text, JSON and HTML.",
        }),
        _entry("Chat commands", "", **{
            "/help": "Show the short command list in chat.",
            "/place Name, Terrain, Description": "Add a location to the map. Terrain: Forest, City, Ruins, "
                                                 "Underground, Ocean, Mountains, Plains, Desert, Swamp.",
            "*add location: Name, local|country|continent|universe*": "Add a location at a chosen map scale.",
        }),
        _entry("Message actions", "Hover a chat message for its buttons.", **{
            "Copy / Paste to input / Select": "Reuse the text.",
            "Edit": "Change the message.",
            "Delete": "Remove this message.",
            "Rewind": "Delete this message and everything after it.",
            "Regenerate": "Ask the storyteller for a different reply.",
            "Progress story forward": "Continue the story from here.",
            "Generate media": "Make an image from the message.",
            "Save to memory": "Pin the message as a fact for this story.",
        }),
        _entry("How replies are formatted", "“Name: text” is dialogue. **Bold text** is action or narration."),
        _entry("Party", "Click a party member to speak as them; “Narrator” returns to the storyteller. "
               "“Recruit companion” adds a saved character (up to 6 in the party) and can delete saved characters."),
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
               **{_stat(k): STAT_MEANINGS.get(k, "") for k in levelling.STAT_NAMES}),
        _entry("Ability modifier", "(score − 10) ÷ 2, rounded down. A score of 10–11 gives +0, 14–15 gives +2, "
               "18–19 gives +4. Modifiers, not raw scores, are added to rolls."),
        _entry("Proficiency bonus", "Added to attack rolls. It grows with level.", **prof_rows),
        _entry("Hit points and mana", "Outside combat: max HP = 20 + 8 per level + Constitution modifier per level; "
               "max mana = 10 + 4 per level + the better of your Intelligence or Wisdom modifier per level. "
               "In tactical combat HP follows the class hit die: full die + CON modifier at level 1, then half the "
               "die + 1 + CON modifier for each further level."),
        _entry("Experience and levels", "XP comes from completing quests and practice actions. Reaching a threshold "
               "raises your level immediately and queues a level-up choice.", **xp_rows),
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
               }),
        _entry("Resting", "Short Rest takes 1 hour and restores 25% of maximum HP and mana. Long Rest takes 8 hours "
               "and restores everything. Both apply to the whole party and advance the world clock."),
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
               "Two allies fight beside you and act on their own; enemies are controlled by the game."),
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
               }),
        _entry("Attack rolls", "Roll d20 + ability modifier + proficiency bonus. The attack hits if the total "
               "equals or beats the target's Armour Class (AC). Strength is used for melee, Dexterity for finesse "
               "and ranged weapons. A natural 20 always hits and is a critical hit (weapon dice are doubled). "
               "A natural 1 always misses."),
        _entry("Armour Class", "Your AC is 10 + Dexterity modifier + the bonus of your best equipped armour."),
        _entry("Damage", "Weapon dice + ability modifier. A unit at 0 HP is out of the fight."),
        _entry("Advantage and disadvantage", "Advantage rolls two d20 and keeps the higher; disadvantage keeps "
               "the lower."),
        _entry("Range and cover", "Melee weapons reach 1 tile, reach weapons 2, ranged weapons 4. Higher-tier "
               "weapons without a D&D entry reach 3 tiles (tiers 4–6) or 5 (tier 7+). Ranged attacks need a clear "
               "line; obstacles block them and block movement."),
        _entry("Opportunity attacks", "Leaving a melee enemy's reach lets it attack you once per round as a "
               "reaction, unless you Disengaged. The same applies to enemies leaving yours."),
        _entry("Extra attack", "Fighters, Paladins, Rangers, Barbarians and Monks may attack twice with one Action."),
        _entry("Power attack", "With Great Weapon Master (melee) or Sharpshooter (ranged) you may take −5 to hit "
               "for +10 damage."),
        _entry("Falling to 0 HP", "Your character falls unconscious and makes a death saving throw each turn: "
               "10 or more is a success, less is a failure, a 1 counts as two failures, and a 20 puts you back on "
               "1 HP. Three successes stabilise you; three failures mean death."),
        _entry("Spell slots", "Full casters use this table; Paladins and Rangers count as half their level. "
               "Classes that are not casters have no slots.", **slot_rows),
        _entry("Winning and losing", "You win when every enemy is down and lose when your whole side is. "
               "Result & End closes the encounter."),
        _entry("Enemies by danger", "The world's Danger rating decides how many enemies appear (2 to 6) and which "
               "kinds.", **danger_rows),
    ]}


def _classes() -> dict:
    tiers = levelling.PROFESSION_TIERS
    levels = sorted(tiers)
    base_level = levels[1]
    entries = []
    for i, name in enumerate(tiers[base_level]):
        path = [tiers[lv][i] for lv in levels[1:] if i < len(tiers[lv])]
        key = name.lower()
        casting = spells.CASTING_ABILITY_BY_PROFESSION.get(name)
        entries.append(_entry(name, CLASS_BLURBS.get(name, ""), **{
            "Hit die": f"d{levelling.get_hit_die(name)}",
            "Spellcaster": "Yes — offered spells every 2 levels" if levelling.is_caster(key) else "No — offered spells every 4 levels",
            "Casting ability": _stat(casting) if casting else "",
            "Two attacks per Action": "Yes" if tactical_combat._has_extra_attack(name) else "",
            "Class path": " → ".join(f"{p} (level {lv})" for p, lv in zip(path, levels[1:])),
        }))
    entries.append(_entry("Starting titles", "Before level 5 a character holds a beginner title and uses a d6 hit die.",
                          **{"Titles": _join(tiers[levels[0]])}))
    entries.append(_entry("Changing class", "At levels 5, 10, 15 and 20 the level-up screen offers the classes of "
                          "that tier. Each tier is a stronger form of the one before it."))
    entries.append(_entry("Occupations", "The character builder also offers everyday and fantasy occupations. "
                          "They describe who the character is; one whose name matches a class above uses that "
                          "class's hit die.", **{"Occupations": _join(PROFESSIONS)}))
    return {"id": "classes", "title": "Classes", "intro": "A class sets your hit die, whether you cast spells, and your upgrade path.", "entries": entries}


def _races() -> dict:
    entries = []
    for name, race in DND_RACES.items():
        entries.append(_entry(name, race.get("lore", ""), **{
            "Ability bonuses": _join(f"{k} {v}" for k, v in (race.get("stat_bonuses") or {}).items()),
            "Features": _join(race.get("features", [])),
            "Traits": _join(race.get("traits", [])),
            "Speed": f"{race['speed']} ft" if race.get("speed") else "",
            "Size": race.get("size", ""),
            "Languages": _join(race.get("languages", [])),
            "Lifespan": race.get("age_range", ""),
        }))
    return {"id": "races", "title": "Races", "intro": f"{len(entries)} playable races. Each gives ability bonuses and innate features.", "entries": entries}


def _feats() -> dict:
    entries = []
    for name, feat in levelling.DND_FEATS.items():
        prereq = feat.get("prereq")
        if prereq:
            stat, _, value = str(prereq).partition(">=")
            prereq = f"{_stat(stat)} {value} or higher"
        entries.append(_entry(name, feat.get("desc", ""), **{
            "Category": str(feat.get("category", "")).title(),
            "Requires": prereq or "",
            "Bonus": _join(f"+{v} {_stat(k)}" for k, v in (feat.get("bonus") or {}).items()),
            "In tactical combat": "Has a direct effect in fights" if name in tactical_combat.COMBAT_FEATS else "",
        }))
    return {"id": "feats", "title": "Feats", "intro": "Special talents. You can take one in place of an Ability Score "
            f"Improvement at levels {_join(sorted(levelling.ASI_LEVELS))}, or earn one from a quest.", "entries": entries}


def _spells() -> dict:
    entries = [_entry("Spell levels", "Level 0 spells are cantrips and cost nothing to cast. Level 1 and higher "
                      "spells use a spell slot of that level in combat. You learn spells at level-up and from quests."),
               _entry("Casting ability", "The ability that powers a class's spells.", **{
                   _stat(ability): _join(k for k, v in spells.CASTING_ABILITY_BY_PROFESSION.items() if v == ability)
                   for ability in dict.fromkeys(spells.CASTING_ABILITY_BY_PROFESSION.values())}),
               _entry("Schools of magic", "", **{s: SCHOOL_BLURBS.get(s, "") for s in spells.SPELL_SCHOOLS})]
    for name, spell in sorted(spells.SPELLS.items(), key=lambda kv: (kv[1].get("level", 0), kv[0])):
        level = spell.get("level", 0)
        entries.append(_entry(name, spell.get("description", ""), **{
            "Level": "Cantrip" if level == 0 else f"Level {level}",
            "School": spell.get("school", ""),
            "Classes": _join(spell.get("classes", [])),
            "Casting time": spell.get("casting_time", ""),
            "Range": spell.get("range", ""),
            "Duration": spell.get("duration", ""),
            "Components": spell.get("components", ""),
            "Damage": f"{spell['damage']} {spell.get('damage_type', '')}".strip() if spell.get("damage") else "",
            "Healing": spell.get("heal", ""),
            "Saving throw": _stat(spell["save_ability"]) if spell.get("save_ability") else "",
            "AC bonus": f"+{spell['ac_bonus']}" if spell.get("ac_bonus") else "",
            "Always hits": "Yes" if spell.get("auto_hit") else "",
        }))
    return {"id": "spells", "title": "Spells", "intro": f"{len(spells.SPELLS)} spells across {len(spells.SPELL_SCHOOLS)} schools.", "entries": entries}


def _skill_tree() -> dict:
    nodes = skill_tree_data.ALL_NODES
    entries = [_entry("Unlocking abilities", "An ability can be unlocked when you meet its level and ability-score "
                      "requirements and already have every ability it builds on. Unlock them from the Skill Tree "
                      "panel or as a level-up choice.")]
    for category in skill_tree_data.CATEGORIES:
        label = skill_tree_data.CATEGORY_LABELS.get(category, category.title())
        for node in sorted((n for n in nodes.values() if n["category"] == category), key=lambda n: (n["tier"], n["level_req"], n["name"])):
            entries.append(_entry(node["name"], node.get("desc", ""), **{
                "Branch": label,
                "Tier": node["tier"],
                "Requires level": node["level_req"],
                "Requires": _join(f"{_stat(k)} {v}" for k, v in node.get("attr_req", {}).items()),
                "Builds on": _join(nodes[p]["name"] for p in node.get("parents", []) if p in nodes),
            }))
    return {"id": "skilltree", "title": "Skill tree", "intro": f"{len(nodes)} abilities in {len(skill_tree_data.CATEGORIES)} branches and 4 tiers.", "entries": entries}


def _character_options() -> dict:
    return {"id": "character", "title": "Character options", "intro": "Choices on the character builder.", "entries": [
        _entry("Alignment", "A character's moral outlook, on two axes: Lawful–Chaotic and Good–Evil.",
               **{a: ALIGNMENT_BLURBS.get(a, "") for a in ALIGNMENTS}),
        _entry("Backgrounds", "What the character did before the story began. It colours how the storyteller "
               "writes them.", **{"Backgrounds": _join(DND_BACKGROUNDS)}),
        _entry("Skills", "Things the character is practised at. The storyteller takes them into account when "
               "describing what you attempt.", **{"Skills": _join(SKILLS_LIST)}),
        _entry("Quirks", "Small habits that make a character distinctive.", **{"Quirks": _join(QUIRKS_LIST)}),
        _entry("Magic types", "The flavour of magic a character uses.", **{"Types": _join(MAGIC_TYPES)}),
        _entry("Power systems", "Where a character's power comes from, for settings that are not plain D&D.",
               **{"Systems": _join(POWER_SYSTEMS)}),
        _entry("Origins", "The kind of world the character comes from.", **{"Origins": _join(multiverse.CHARACTER_ORIGINS)}),
        _entry("Power tier", "A rough ceiling on how powerful a character is.",
               **{f"Tier {t['tier']} — {t['name']}": t["scope"] for t in multiverse.POWER_TIERS}),
        _entry("Values", "Eight sliders from 0 to 100 describing what the character believes in.",
               **{k.replace("_", " ").title(): v for k, v in multiverse.VALUES_AXES.items()}),
    ]}


def _tags() -> dict:
    entries = [_entry("What tags do", "Tags label a character's role, personality, genre and themes. They are used "
                      "to organise and search characters, and some set how much a character trusts you at the "
                      "start. Tags never override the content limits: no sexual content involving anyone under 18.")]
    placed: set[str] = set()
    trust = relationship_engine.TAG_TRUST_MAP
    for title, blurb, names in TAG_GROUPS:
        present = [t for t in names if t in CHARACTER_TAGS]
        placed.update(present)
        fields = {t: TAG_DEFINITIONS[t] for t in present if t in TAG_DEFINITIONS}
        fields["Tags"] = _join(present)
        starting = _join(f"{t} {trust[t]}" for t in present if t in trust)
        if starting:
            fields["Starting trust (0–100)"] = starting
        entries.append(_entry(title, blurb, **fields))
    rest = [t for t in CHARACTER_TAGS if t not in placed]
    if rest:
        fields = {t: TAG_DEFINITIONS[t] for t in rest if t in TAG_DEFINITIONS}
        fields["Tags"] = _join(rest)
        entries.append(_entry("Other", "", **fields))
    return {"id": "tags", "title": "Tags", "intro": f"{len(CHARACTER_TAGS)} tags in groups.", "entries": entries}


def _equipment() -> dict:
    entries = [_entry("Weapon properties", "", **{p.replace("_", "-"): WEAPON_PROPERTY_BLURBS.get(p, "")
                                                  for p in sorted({p for w in dnd_weapons.DND_WEAPONS.values() for p in w.get("properties", [])})}),
               _entry("Equipping", "Equip items from the Inventory panel. An equipped weapon sets your attack "
                      "damage and range in combat; equipped armour raises your Armour Class.")]
    for name, weapon in dnd_weapons.DND_WEAPONS.items():
        entries.append(_entry(name, "", **{
            "Category": weapon.get("category", ""),
            "Damage": f"{weapon.get('damage', '')} {weapon.get('damage_type', '')}".strip(),
            "Properties": _join(p.replace("_", "-") for p in weapon.get("properties", [])),
            "Weapon tier": weapon.get("tier", ""),
        }))
    for tier in weapons.WEAPON_TIERS:
        entries.append(_entry(f"Weapon tier {tier['tier']} — {tier['era']}", "A world's Weapon rating is the "
                              "highest tier normally available there.", **{
                                  "Examples": _join(tier.get("examples", [])),
                                  "Strengths": _join(tier.get("properties", [])),
                                  "Limitations": _join(tier.get("limitations", [])),
                              }))
    return {"id": "equipment", "title": "Weapons and equipment", "intro": f"{len(dnd_weapons.DND_WEAPONS)} D&D weapons and {len(weapons.WEAPON_TIERS)} technology tiers.", "entries": entries}


def _monsters() -> dict:
    entries = []
    for name, m in sorted(tactical_combat.DND_MONSTERS.items(), key=lambda kv: (kv[1].get("cr", 0), kv[0])):
        entries.append(_entry(name, "", **{
            "Challenge rating": m.get("cr", ""),
            "Hit points": m.get("hp", ""),
            "Armour Class": m.get("ac", ""),
            "Damage": m.get("damage", ""),
            "Weapon": m.get("weapon", ""),
            "Movement": f"{m['speed']} tiles" if m.get("speed") else "",
        }))
    return {"id": "monsters", "title": "Monsters", "intro": "Enemies that can appear in tactical combat.", "entries": entries}


def _quests() -> dict:
    entries = [
        _entry("Getting quests", "Generate (in the quest bar) asks the storyteller for a quest based on your recent "
               "chat. A story quest is also offered automatically every 8 replies while you have fewer than 4. "
               "Locations can offer quests of their own. If the storyteller is unavailable a simple templated "
               "quest is created instead."),
        _entry("Completing quests", "Mark a quest complete from the quest bar. You receive its XP and one reward "
               "drawn from that quest type's list. Abandoning a quest gives nothing."),
        _entry("Quests belong to a character", "Each character has their own quests, even when two characters "
               "share a name."),
    ]
    for qtype in quest_system.QUEST_TYPES:
        entries.append(_entry(f"{qtype.title()} quest", QUEST_TYPE_BLURBS.get(qtype, ""), **{
            "XP": quest_system._QXP.get(qtype, 40),
            "Possible rewards": _join(r.replace("_", " ") for r in quest_system._REWARD_POOL.get(qtype, [])),
        }))
    entries.append(_entry("Reward types", "", **{k.replace("_", " ").title(): v for k, v in REWARD_BLURBS.items()}))
    return {"id": "quests", "title": "Quests and rewards", "intro": "How quests are created and what they pay.", "entries": entries}


def _relationships() -> dict:
    return {"id": "relationships", "title": "Relationships", "intro": "How characters come to trust you.", "entries": [
        _entry("Trust", "Each character you talk to has a trust score from 0 to 100, starting at 50 unless their "
               "tags say otherwise. It is tracked separately in each story."),
        _entry("What changes trust", "", **{
            "Friendly message": "+3", "Hostile message": "−4", "Help": "+5", "Gift": "+8", "Flirt": "+4",
            "Quest completed": "+5", "Insult": "−6", "Attack": "−10", "Betrayal": "−15",
        }),
        _entry("Bond", "The relationship label, set by trust.", **{
            "Stranger": "below 15", "Acquaintance": "15–34", "Friend": "35–54", "Close friend": "55–74",
            "Trusted ally": "75–89", "Soulbound": "90 or more",
        }),
        _entry("Mood", "How the character feels towards you, set by trust.", **{
            "Hostile": "below 10", "Annoyed": "10–19", "Neutral": "20–39", "Pleasant": "40–59",
            "Happy": "60–79", "Elated": "80 or more",
        }),
        _entry("Memory", "The storyteller remembers what happens in a story and brings it back later. Memories "
               "stay inside their story. “Save to memory” on a chat message pins it for that story."),
    ]}


def _worlds() -> dict:
    entries = [_entry("World ratings", "Every world is rated 0–10 on eight axes. They tell the storyteller what "
                      "is possible there and decide things like the weapons and enemies you meet.")]
    for axis, description in worldscale.WORLD_AXES.items():
        labels = worldscale.AXIS_LEVEL_LABELS.get(axis, [])
        entries.append(_entry(f"{axis.title()} rating", description, **{str(i): label for i, label in enumerate(labels)}))
    entries.append(_entry("Reality types", "How a world relates to others in the multiverse.", **dict(multiverse.REALITY_TYPES)))
    entries.append(_entry("Travelling between worlds", "Use the portal on the map or the Universe tab. "
                          "A world's ratings apply as soon as you arrive."))
    entries.append(_entry("Time, weather and threat", "The bar under the map shows the time of day, day count, "
                          "weather and threat level. Resting and +30m advance the clock."))
    return {"id": "worlds", "title": "Worlds and the multiverse", "intro": "World ratings and travel.", "entries": entries}


def _content_limits() -> dict:
    return {"id": "limits", "title": "Content limits", "intro": "What the storyteller will not write.", "entries": [
        _entry("Always enforced", "The storyteller narrates action, conflict, romance and dark themes as the story "
               "calls for them. It does not write scenes that sexualise minors, or non-consensual scenarios "
               "involving real, identifiable living people. No tag, scenario or setting changes this."),
    ]}


def build_help() -> list[dict]:
    """Every Help section, in display order."""
    return [
        _getting_started(), _controls(), _core_rules(), _combat(), _classes(), _races(), _feats(), _spells(),
        _skill_tree(), _character_options(), _tags(), _equipment(), _monsters(), _quests(), _relationships(),
        _worlds(), _content_limits(),
    ]
