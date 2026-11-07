"""SRD-derived spellbook: cantrips through 5th level, spanning all six SRD
schools of magic. Each entry carries enough structure to actually resolve
in combat (attack roll + damage, saving throw + damage/effect, healing, or
a flavor-only utility/buff), not just a display name.

Content is written to describe the same spells named in the CC-BY-4.0
SRD 5.2.1 (see knowledge/dnd/00_srd_5_2_1_notice.md) -- names and short
mechanical summaries only, not the SRD's own prose.
"""
from __future__ import annotations

# effect_type: "attack" (spell attack roll vs AC), "save" (target saves vs
# spell DC), "heal" (restores hp), "utility"/"buff" (no direct combat math;
# logged narratively).
SPELLS = {
    # ── Cantrips (level 0) ──
    "Fire Bolt": {"level": 0, "school": "Evocation", "classes": ["Wizard", "Sorcerer"],
                  "casting_time": "1 action", "range": "120 ft", "components": "V, S", "duration": "Instantaneous",
                  "effect_type": "attack", "damage": "1d10", "damage_type": "fire",
                  "description": "A mote of fire streaks toward a target within range."},
    "Ray of Frost": {"level": 0, "school": "Evocation", "classes": ["Wizard", "Sorcerer"],
                     "casting_time": "1 action", "range": "60 ft", "components": "V, S", "duration": "Instantaneous",
                     "effect_type": "attack", "damage": "1d8", "damage_type": "cold",
                     "description": "A frigid beam of blue-white light streaks toward a target, chilling it."},
    "Sacred Flame": {"level": 0, "school": "Evocation", "classes": ["Priest"],
                     "casting_time": "1 action", "range": "60 ft", "components": "V, S", "duration": "Instantaneous",
                     "effect_type": "save", "save_ability": "dexterity", "damage": "1d8", "damage_type": "radiant",
                     "description": "Flame-like radiance descends on a creature, which must dodge or burn."},
    "Eldritch Blast": {"level": 0, "school": "Evocation", "classes": ["Summoner"],
                       "casting_time": "1 action", "range": "120 ft", "components": "V, S", "duration": "Instantaneous",
                       "effect_type": "attack", "damage": "1d10", "damage_type": "force",
                       "description": "A beam of crackling energy streaks toward a creature."},
    "Vicious Mockery": {"level": 0, "school": "Enchantment", "classes": ["Bard"],
                        "casting_time": "1 action", "range": "60 ft", "components": "V", "duration": "Instantaneous",
                        "effect_type": "save", "save_ability": "wisdom", "damage": "1d4", "damage_type": "psychic",
                        "description": "Insults laced with subtle magic sting the target's mind."},
    "Poison Spray": {"level": 0, "school": "Conjuration", "classes": ["Wizard", "Necromancer"],
                     "casting_time": "1 action", "range": "10 ft", "components": "V, S", "duration": "Instantaneous",
                     "effect_type": "save", "save_ability": "constitution", "damage": "1d12", "damage_type": "poison",
                     "description": "A puff of noxious gas sprays from your hand."},
    "Minor Illusion": {"level": 0, "school": "Illusion", "classes": ["Wizard", "Bard"],
                       "casting_time": "1 action", "range": "30 ft", "components": "S, M", "duration": "1 minute",
                       "effect_type": "utility",
                       "description": "Creates a harmless sound or image, useful for distraction."},
    "Guidance": {"level": 0, "school": "Divination", "classes": ["Priest", "Healer"],
                "casting_time": "1 action", "range": "Touch", "components": "V, S", "duration": "Concentration, 1 min",
                "effect_type": "buff",
                "description": "Touch a willing creature; it may add 1d4 to one ability check."},

    # ── Level 1 ──
    "Magic Missile": {"level": 1, "school": "Evocation", "classes": ["Wizard", "Sorcerer"],
                      "casting_time": "1 action", "range": "120 ft", "components": "V, S", "duration": "Instantaneous",
                      "effect_type": "attack", "auto_hit": True, "damage": "3d4+3", "damage_type": "force",
                      "description": "Three darts of magical force strike unerringly."},
    "Burning Hands": {"level": 1, "school": "Evocation", "classes": ["Wizard", "Sorcerer"],
                      "casting_time": "1 action", "range": "Self (15-ft cone)", "components": "V, S", "duration": "Instantaneous",
                      "effect_type": "save", "save_ability": "dexterity", "damage": "3d6", "damage_type": "fire",
                      "description": "A thin sheet of flame shoots from your outstretched fingertips."},
    "Guiding Bolt": {"level": 1, "school": "Evocation", "classes": ["Priest"],
                     "casting_time": "1 action", "range": "120 ft", "components": "V, S", "duration": "1 round",
                     "effect_type": "attack", "damage": "4d6", "damage_type": "radiant",
                     "description": "A flash of light streaks toward a creature."},
    "Cure Wounds": {"level": 1, "school": "Abjuration", "classes": ["Priest", "Healer", "Bard"],
                    "casting_time": "1 action", "range": "Touch", "components": "V, S", "duration": "Instantaneous",
                    "effect_type": "heal", "heal": "1d8+3",
                    "description": "A creature you touch regains hit points."},
    "Healing Word": {"level": 1, "school": "Abjuration", "classes": ["Priest", "Healer", "Bard"],
                     "casting_time": "1 bonus action", "range": "60 ft", "components": "V", "duration": "Instantaneous",
                     "effect_type": "heal", "heal": "1d4+3",
                     "description": "A creature of your choice regains hit points at a distance."},
    "Shield": {"level": 1, "school": "Abjuration", "classes": ["Wizard", "Sorcerer"],
              "casting_time": "1 reaction", "range": "Self", "components": "V, S", "duration": "1 round",
              "effect_type": "buff", "ac_bonus": 5,
              "description": "An invisible barrier of magical force adds to your AC until your next turn."},
    "Sleep": {"level": 1, "school": "Enchantment", "classes": ["Wizard", "Sorcerer", "Bard"],
             "casting_time": "1 action", "range": "90 ft", "components": "V, S, M", "duration": "1 minute",
             "effect_type": "save", "save_ability": "wisdom", "damage": "5d8", "damage_type": "psychic",
             "description": "This spell sends creatures into a magical slumber (modeled as psychic damage/disable)."},
    "Thunderwave": {"level": 1, "school": "Evocation", "classes": ["Wizard", "Sorcerer"],
                    "casting_time": "1 action", "range": "Self (15-ft cube)", "components": "V, S", "duration": "Instantaneous",
                    "effect_type": "save", "save_ability": "constitution", "damage": "2d8", "damage_type": "thunder",
                    "description": "A wave of thunderous force sweeps out from you."},

    # ── Level 2 ──
    "Scorching Ray": {"level": 2, "school": "Evocation", "classes": ["Wizard", "Sorcerer"],
                      "casting_time": "1 action", "range": "120 ft", "components": "V, S", "duration": "Instantaneous",
                      "effect_type": "attack", "damage": "2d6", "damage_type": "fire",
                      "description": "You create three rays of fire and hurl them at targets."},
    "Hold Person": {"level": 2, "school": "Enchantment", "classes": ["Wizard", "Priest", "Bard"],
                    "casting_time": "1 action", "range": "60 ft", "components": "V, S, M", "duration": "Concentration, 1 min",
                    "effect_type": "save", "save_ability": "wisdom", "damage": "0", "damage_type": None,
                    "description": "A humanoid must succeed on a Wisdom save or be paralyzed."},
    "Misty Step": {"level": 2, "school": "Conjuration", "classes": ["Wizard", "Sorcerer"],
                  "casting_time": "1 bonus action", "range": "Self", "components": "V", "duration": "Instantaneous",
                  "effect_type": "utility", "teleport": True,
                  "description": "You teleport up to 30 feet to an unoccupied space you can see."},
    "Spiritual Weapon": {"level": 2, "school": "Evocation", "classes": ["Priest"],
                        "casting_time": "1 bonus action", "range": "60 ft", "components": "V, S", "duration": "1 minute",
                        "effect_type": "attack", "damage": "1d8+3", "damage_type": "force",
                        "description": "A spectral weapon appears and strikes at your command."},
    "Web": {"level": 2, "school": "Conjuration", "classes": ["Wizard", "Sorcerer"],
           "casting_time": "1 action", "range": "60 ft", "components": "V, S, M", "duration": "Concentration, 1 hour",
           "effect_type": "save", "save_ability": "dexterity", "damage": "0", "damage_type": None,
           "description": "Thick, sticky webbing fills the area, restraining those caught in it."},

    # ── Level 3 ──
    "Fireball": {"level": 3, "school": "Evocation", "classes": ["Wizard", "Sorcerer"],
                "casting_time": "1 action", "range": "150 ft", "components": "V, S, M", "duration": "Instantaneous",
                "effect_type": "save", "save_ability": "dexterity", "damage": "8d6", "damage_type": "fire",
                "description": "A bright streak flashes to a point and blossoms into a roaring fire."},
    "Lightning Bolt": {"level": 3, "school": "Evocation", "classes": ["Wizard", "Sorcerer"],
                      "casting_time": "1 action", "range": "Self (100-ft line)", "components": "V, S, M", "duration": "Instantaneous",
                      "effect_type": "save", "save_ability": "dexterity", "damage": "8d6", "damage_type": "lightning",
                      "description": "A stroke of lightning forming a line blasts out from you."},
    "Counterspell": {"level": 3, "school": "Abjuration", "classes": ["Wizard", "Sorcerer"],
                     "casting_time": "1 reaction", "range": "60 ft", "components": "S", "duration": "Instantaneous",
                     "effect_type": "utility",
                     "description": "You attempt to interrupt a creature in the process of casting a spell."},
    "Haste": {"level": 3, "school": "Transmutation", "classes": ["Wizard", "Sorcerer"],
             "casting_time": "1 action", "range": "30 ft", "components": "V, S, M", "duration": "Concentration, 1 min",
             "effect_type": "buff", "ac_bonus": 2,
             "description": "A willing creature's speed doubles and it gains a bonus to AC."},
    "Mass Healing Word": {"level": 3, "school": "Abjuration", "classes": ["Priest", "Healer"],
                          "casting_time": "1 bonus action", "range": "60 ft", "components": "V", "duration": "Instantaneous",
                          "effect_type": "heal", "heal": "1d4+3",
                          "description": "Words of creation heal up to six creatures of your choice."},

    # ── Level 4 ──
    "Ice Storm": {"level": 4, "school": "Evocation", "classes": ["Wizard", "Sorcerer"],
                 "casting_time": "1 action", "range": "300 ft", "components": "V, S, M", "duration": "Instantaneous",
                 "effect_type": "save", "save_ability": "dexterity", "damage": "4d6+2d8", "damage_type": "cold",
                 "description": "A hail of rock-hard ice pounds the ground in a cylinder centered on a point."},
    "Polymorph": {"level": 4, "school": "Transmutation", "classes": ["Wizard", "Priest"],
                 "casting_time": "1 action", "range": "60 ft", "components": "V, S, M", "duration": "Concentration, 1 hour",
                 "effect_type": "save", "save_ability": "wisdom", "damage": "0", "damage_type": None,
                 "description": "You transform a creature into a new form."},
    "Wall of Fire": {"level": 4, "school": "Evocation", "classes": ["Wizard", "Sorcerer"],
                     "casting_time": "1 action", "range": "120 ft", "components": "V, S, M", "duration": "Concentration, 1 min",
                     "effect_type": "save", "save_ability": "dexterity", "damage": "5d8", "damage_type": "fire",
                     "description": "You create a wall of roaring flame on a solid surface."},

    # ── Level 5 ──
    "Cone of Cold": {"level": 5, "school": "Evocation", "classes": ["Wizard", "Sorcerer"],
                     "casting_time": "1 action", "range": "Self (60-ft cone)", "components": "V, S, M", "duration": "Instantaneous",
                     "effect_type": "save", "save_ability": "constitution", "damage": "8d8", "damage_type": "cold",
                     "description": "A blast of cold air erupts from your hands."},
    "Mass Cure Wounds": {"level": 5, "school": "Abjuration", "classes": ["Priest", "Healer"],
                        "casting_time": "1 action", "range": "60 ft", "components": "V, S", "duration": "Instantaneous",
                        "effect_type": "heal", "heal": "3d8+5",
                        "description": "A wave of healing energy washes out from a point of your choosing."},
    "Hold Monster": {"level": 5, "school": "Enchantment", "classes": ["Wizard", "Priest"],
                     "casting_time": "1 action", "range": "90 ft", "components": "V, S, M", "duration": "Concentration, 1 min",
                     "effect_type": "save", "save_ability": "wisdom", "damage": "0", "damage_type": None,
                     "description": "A creature must succeed on a Wisdom save or be paralyzed."},
}

SPELL_LEVELS = sorted({s["level"] for s in SPELLS.values()})
SPELL_SCHOOLS = sorted({s["school"] for s in SPELLS.values()})


def spells_for_class(profession: str) -> list[str]:
    """Spells whose class list mentions this profession, or all spells if
    the profession isn't a recognized spellcasting one (lets any character
    browse the full list rather than being locked out)."""
    matches = [name for name, s in SPELLS.items() if profession in s.get("classes", [])]
    return matches or list(SPELLS.keys())


# Profession -> spellcasting ability, used to compute spell attack/DC bonus.
CASTING_ABILITY_BY_PROFESSION = {
    "Wizard": "intelligence", "Necromancer": "intelligence", "Artificer": "intelligence", "Scholar": "intelligence",
    "Priest": "wisdom", "Healer": "wisdom", "Ranger": "wisdom", "Monk": "wisdom", "Exorcist": "wisdom", "Druid": "wisdom",
    "Bard": "charisma_stat", "Summoner": "charisma_stat", "Diplomat": "charisma_stat", "Courtesan": "charisma_stat",
}


def casting_ability_for(profession: str) -> str:
    return CASTING_ABILITY_BY_PROFESSION.get(profession, "intelligence")
