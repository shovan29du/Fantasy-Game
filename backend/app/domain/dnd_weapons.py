"""SRD-derived weapon list: simple and martial, melee and ranged, with real
damage dice and properties. Distinct from domain.weapons (the 0-10
multiverse weapon-tier system spanning improvised rocks to cosmic
armaments) -- these are the tier-1/2/3 (primitive/ancient/medieval) entries
of that system, given full D&D-style stat blocks so weapon attacks in
combat use real dice instead of a flat generic roll.
"""
from __future__ import annotations

# properties: finesse (may use Dex instead of Str), light, heavy, reach,
# thrown, two_handed, versatile, ammunition.
DND_WEAPONS = {
    # ── Simple Melee ──
    "Club": {"category": "Simple Melee", "damage": "1d4", "damage_type": "bludgeoning",
              "properties": ["light"], "tier": 1},
    "Dagger": {"category": "Simple Melee", "damage": "1d4", "damage_type": "piercing",
               "properties": ["finesse", "light", "thrown"], "range": "20/60", "tier": 2},
    "Quarterstaff": {"category": "Simple Melee", "damage": "1d6", "damage_type": "bludgeoning",
                     "properties": ["versatile"], "versatile_damage": "1d8", "tier": 2},
    "Spear": {"category": "Simple Melee", "damage": "1d6", "damage_type": "piercing",
              "properties": ["thrown", "versatile"], "range": "20/60", "versatile_damage": "1d8", "tier": 2},
    "Handaxe": {"category": "Simple Melee", "damage": "1d6", "damage_type": "slashing",
                "properties": ["light", "thrown"], "range": "20/60", "tier": 2},
    "Mace": {"category": "Simple Melee", "damage": "1d6", "damage_type": "bludgeoning",
             "properties": [], "tier": 2},
    "Sickle": {"category": "Simple Melee", "damage": "1d4", "damage_type": "slashing",
               "properties": ["light", "finesse"], "tier": 2},

    # ── Simple Ranged ──
    "Shortbow": {"category": "Simple Ranged", "damage": "1d6", "damage_type": "piercing",
                "properties": ["ammunition", "two_handed"], "range": "80/320", "tier": 2},
    "Light Crossbow": {"category": "Simple Ranged", "damage": "1d8", "damage_type": "piercing",
                       "properties": ["ammunition", "two_handed"], "range": "80/320", "tier": 3},
    "Sling": {"category": "Simple Ranged", "damage": "1d4", "damage_type": "bludgeoning",
              "properties": ["ammunition"], "range": "30/120", "tier": 1},
    "Dart": {"category": "Simple Ranged", "damage": "1d4", "damage_type": "piercing",
             "properties": ["finesse", "thrown"], "range": "20/60", "tier": 1},

    # ── Martial Melee ──
    "Shortsword": {"category": "Martial Melee", "damage": "1d6", "damage_type": "piercing",
                  "properties": ["finesse", "light"], "tier": 2},
    "Rapier": {"category": "Martial Melee", "damage": "1d8", "damage_type": "piercing",
              "properties": ["finesse"], "tier": 2},
    "Longsword": {"category": "Martial Melee", "damage": "1d8", "damage_type": "slashing",
                 "properties": ["versatile"], "versatile_damage": "1d10", "tier": 2},
    "Scimitar": {"category": "Martial Melee", "damage": "1d6", "damage_type": "slashing",
                "properties": ["finesse", "light"], "tier": 2},
    "Battleaxe": {"category": "Martial Melee", "damage": "1d8", "damage_type": "slashing",
                 "properties": ["versatile"], "versatile_damage": "1d10", "tier": 2},
    "Warhammer": {"category": "Martial Melee", "damage": "1d8", "damage_type": "bludgeoning",
                 "properties": ["versatile"], "versatile_damage": "1d10", "tier": 2},
    "Greataxe": {"category": "Martial Melee", "damage": "1d12", "damage_type": "slashing",
                "properties": ["heavy", "two_handed"], "tier": 3},
    "Greatsword": {"category": "Martial Melee", "damage": "2d6", "damage_type": "slashing",
                  "properties": ["heavy", "two_handed"], "tier": 3},
    "Halberd": {"category": "Martial Melee", "damage": "1d10", "damage_type": "slashing",
               "properties": ["heavy", "reach", "two_handed"], "tier": 3},
    "Whip": {"category": "Martial Melee", "damage": "1d4", "damage_type": "slashing",
             "properties": ["finesse", "reach"], "tier": 2},

    # ── Martial Ranged ──
    "Longbow": {"category": "Martial Ranged", "damage": "1d8", "damage_type": "piercing",
               "properties": ["ammunition", "heavy", "two_handed"], "range": "150/600", "tier": 2},
    "Heavy Crossbow": {"category": "Martial Ranged", "damage": "1d10", "damage_type": "piercing",
                      "properties": ["ammunition", "heavy", "two_handed"], "range": "100/400", "tier": 3},
    "Hand Crossbow": {"category": "Martial Ranged", "damage": "1d6", "damage_type": "piercing",
                     "properties": ["ammunition", "light"], "range": "30/120", "tier": 3},
}

WEAPON_CATEGORIES = sorted({w["category"] for w in DND_WEAPONS.values()})


def is_finesse_or_ranged(weapon_name: str) -> bool:
    weapon = DND_WEAPONS.get(weapon_name)
    if not weapon:
        return False
    return "finesse" in weapon.get("properties", []) or "Ranged" in weapon.get("category", "")


def weapon_tier_for(weapon_name: str) -> int:
    weapon = DND_WEAPONS.get(weapon_name)
    return weapon["tier"] if weapon else 2
