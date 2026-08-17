"""Multiverse structure: reality types, power tiers, reality signatures, and
the translation rules applied when a character or item crosses between
worlds with different world-scale ratings (see domain.worldscale).
"""
from __future__ import annotations

import random

from . import weapons as _weapons
from . import worldscale as _worldscale

# 17 character origin types — where the character came from before this story.
CHARACTER_ORIGINS = [
    "Original fantasy world",
    "Historical Earth",
    "Modern Earth",
    "Zombie apocalypse",
    "Supernatural hidden world",
    "Cyberpunk megacity",
    "Alien civilization",
    "Spacefaring future",
    "Anime-inspired heroic world",
    "Alternate history",
    "Parallel reality",
    "Mirror universe",
    "Destroyed timeline",
    "Magical version of Earth",
    "Simulation",
    "Divine realm",
    "Unknown universe",
]

# Values axes for character morality tracking (each stored as 0-100, 50 = neutral).
VALUES_AXES = {
    "mercy_vs_ruthlessness": "Mercy (100) vs Ruthlessness (0)",
    "order_vs_freedom": "Order (100) vs Freedom (0)",
    "humanity_vs_corruption": "Humanity (100) vs Corruption (0)",
    "nature_vs_industry": "Nature (100) vs Industry (0)",
    "faith_vs_reason": "Faith (100) vs Reason (0)",
    "loyalty_vs_ambition": "Loyalty (100) vs Ambition (0)",
    "secrecy_vs_truth": "Secrecy (100) vs Truth (0)",
    "individual_vs_collective": "Individual (100) vs Collective (0)",
}

REALITY_TYPES = {
    "Prime Reality": "The campaign's original reference universe.",
    "Alternate Reality": "History changed at a particular event.",
    "Parallel Universe": "A separate world with similar foundations.",
    "Mirror Universe": "Familiar people have reversed roles, loyalties, or values.",
    "Branching Timeline": "Created by an important choice or time-travel event.",
    "Pocket Dimension": "A small artificial or magical reality.",
    "Dead Universe": "Civilization or reality has collapsed.",
    "Merged Universe": "Two incompatible realities have collided.",
}
REALITY_TYPE_NAMES = list(REALITY_TYPES.keys())

POWER_TIERS = [
    {"tier": 0, "name": "Civilian", "scope": "Normal person."},
    {"tier": 1, "name": "Trained", "scope": "Soldier, guard, apprentice."},
    {"tier": 2, "name": "Heroic", "scope": "Standard adventurer."},
    {"tier": 3, "name": "Superhuman", "scope": "Powerful mage, mutant, cyborg."},
    {"tier": 4, "name": "Legendary", "scope": "Dragons, archmages, major heroes."},
    {"tier": 5, "name": "Mythic", "scope": "Demigods and world-level entities."},
    {"tier": 6, "name": "Divine", "scope": "Gods and embodiments of concepts."},
    {"tier": 7, "name": "Cosmic", "scope": "Beings affecting planets or timelines."},
    {"tier": 8, "name": "Multiversal", "scope": "Beings affecting multiple realities."},
]
POWER_TIER_BY_NUMBER = {t["tier"]: t for t in POWER_TIERS}
MAX_POWER_TIER = max(POWER_TIER_BY_NUMBER)

DIVINE_DOMAINS = ["War", "Death", "Knowledge", "Nature", "Machines", "Time", "Chaos", "Life", "Fate", "Storms",
                  "Shadows", "Creation"]


def power_tier_for_level(level: int) -> int:
    """Rough default power tier from character level, so a level-1 character
    starts Civilian/Trained and a level-20 legend sits at Legendary/Mythic.
    Characters can still be assigned a tier explicitly (e.g. a god NPC)."""
    level = max(1, int(level or 1))
    if level >= 20: return 5
    if level >= 15: return 4
    if level >= 10: return 3
    if level >= 5: return 2
    if level >= 2: return 1
    return 0


def describe_power_tier(tier: int) -> dict:
    tier = max(0, min(MAX_POWER_TIER, int(tier or 0)))
    return POWER_TIER_BY_NUMBER[tier]


def generate_reality_signature(origin_world: str = "", reality_type: str | None = None) -> dict:
    """A character's Reality Signature: the home universe they carry with
    them, used for portal/paradox/alternate-version rules."""
    reality_type = reality_type if reality_type in REALITY_TYPES else "Prime Reality"
    tag = f"{(origin_world or 'Unknown').strip().replace(' ', '-')[:24]}-{random.randint(100, 999)}{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}"
    return {"origin_world": origin_world or "Unknown", "reality_type": reality_type, "universe_tag": tag}


def alternate_self_encounter_effects() -> list[str]:
    """Possible consequences of meeting an alternate version of yourself,
    for the GM/AI companion to draw from."""
    return [
        "Shared memories bleed through, confusing which of you experienced what.",
        "Psychological stress from confronting a road not taken.",
        "Temporary power resonance while both versions are near each other.",
        "Localized reality instability around the two of you.",
        "A dispute over which of you is the 'real' one.",
        "One version's identity begins to overwrite the other's.",
        "An uneasy cooperation, or an immediate rivalry.",
    ]


def travel_report(origin_ratings: dict, dest_ratings: dict, dest_reality_type: str = "Prime Reality",
                   character_power_tier: int = 2, inventory_weapon_tiers: list[int] | None = None) -> dict:
    """Translation rules applied when crossing from one world to another.
    Returns magic/tech stability warnings, a power-tier dampening note, and
    per-item weapon-tier effects for whatever the traveller is carrying."""
    origin = _worldscale.normalize_ratings(origin_ratings)
    dest = _worldscale.normalize_ratings(dest_ratings)
    effects: list[str] = []

    magic_gap = origin["magic"] - dest["magic"]
    if dest["magic"] == 0 and origin["magic"] > 0:
        effects.append("Magic does not function at all in this reality — spellcasting fails outright.")
    elif magic_gap >= 4:
        effects.append("Magic is unstable here: spells cost more, and there's a chance of a wild surge.")
    elif magic_gap <= -4:
        effects.append("This reality's magic is far stronger than you're used to — local casters outclass you badly.")

    tech_gap = origin["technology"] - dest["technology"]
    if tech_gap >= 4:
        effects.append("Advanced equipment is hard to repair or resupply here; treat batteries/parts as scarce.")
    elif tech_gap <= -4:
        effects.append("Local technology is far beyond anything you've used — expect a steep learning curve.")

    if dest["danger"] >= 8:
        effects.append("This reality is extremely dangerous — expect frequent, severe threats.")
    if dest["horror"] >= 7:
        effects.append("Tone shift: survival horror rules apply, resources are scarcer, and enemies hit harder psychologically.")

    # dest["power"] is a 0-10 world-scale rating; convert it onto the same
    # 0-8 scale as character_power_tier before comparing the two.
    dest_power_cap = round(dest["power"] * MAX_POWER_TIER / 10)
    tier_gap = character_power_tier - dest_power_cap
    if tier_gap >= 3:
        effects.append("Your power is dampened here — this reality's power ceiling is far lower than your tier.")
    elif tier_gap <= -3:
        effects.append("You are badly outmatched — local beings operate well above your power tier.")

    if dest_reality_type == "Mirror Universe":
        effects.append("Familiar faces may have reversed loyalties, allegiances, or morals here.")
    elif dest_reality_type == "Dead Universe":
        effects.append("Civilization has collapsed here — expect ruins, scarce resources, and few (if any) allies.")
    elif dest_reality_type == "Pocket Dimension":
        effects.append("This reality is small and bounded — it may not persist once you leave.")

    item_effects = []
    for item_tier in (inventory_weapon_tiers or []):
        item_effects.append(_weapons.crossing_effect(item_tier, dest["weapon"]))

    if not effects:
        effects.append("The crossing is smooth — this reality is close enough to your own to feel familiar.")

    return {
        "origin_ratings": origin, "dest_ratings": dest, "dest_reality_type": dest_reality_type,
        "effects": effects, "item_effects": item_effects,
    }
