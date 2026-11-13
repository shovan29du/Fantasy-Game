"""Weapon tier system: a single 0-10 scale spanning improvised rocks to
reality-altering cosmic armaments, shared by every world module. Higher tiers
don't just add damage — they add properties (armour penetration, range,
area effect) balanced against limitations (ammo, energy, training, legality)
so a futuristic character doesn't trivialize a fantasy campaign.
"""
from __future__ import annotations

WEAPON_TIERS = [
    {"tier": 0, "era": "Improvised", "examples": ["Rock", "Stick", "Broken bottle"],
     "properties": [], "limitations": ["Fragile", "No armour penetration"]},
    {"tier": 1, "era": "Primitive", "examples": ["Club", "Sling", "Stone spear"],
     "properties": ["Cheap to replace"], "limitations": ["Short range", "Low damage"]},
    {"tier": 2, "era": "Ancient", "examples": ["Sword", "Bow", "Shield", "Metal spear"],
     "properties": ["Reliable", "Silent"], "limitations": ["Requires melee/close range", "Training helps a lot"]},
    {"tier": 3, "era": "Medieval", "examples": ["Crossbow", "Greatsword", "Heavy armour"],
     "properties": ["Improved armour penetration"], "limitations": ["Heavy", "Slow reload (crossbow)"]},
    {"tier": 4, "era": "Early firearms", "examples": ["Musket", "Flintlock pistol", "Cannon"],
     "properties": ["Armour penetration", "Loud, intimidating"], "limitations": ["Very slow reload", "Black powder needed", "Misfires in wet weather"]},
    {"tier": 5, "era": "Industrial", "examples": ["Revolver", "Rifle", "Shotgun", "Machine gun"],
     "properties": ["Rapid fire", "Good range"], "limitations": ["Ammunition supply", "Maintenance", "Legal restrictions"]},
    {"tier": 6, "era": "Modern", "examples": ["Assault rifle", "Sniper rifle", "Explosives"],
     "properties": ["High accuracy", "Area effect (explosives)"], "limitations": ["Ammunition", "Requires training", "Heavily restricted"]},
    {"tier": 7, "era": "Advanced modern", "examples": ["Smart weapons", "Drones", "Powered armour"],
     "properties": ["Guided targeting", "Networked", "Armour integration"], "limitations": ["Needs power/charge", "Needs maintenance", "Expensive, restricted"]},
    {"tier": 8, "era": "Cyberpunk", "examples": ["Railgun", "Monoblade", "Cybernetic weapons"],
     "properties": ["Extreme armour penetration", "Integrated with cybernetics"], "limitations": ["Energy charge", "Cybernetic compatibility required", "Illegal in most jurisdictions"]},
    {"tier": 9, "era": "Futuristic", "examples": ["Laser gun", "Plasma rifle", "Energy blade"],
     "properties": ["Ignores conventional armour", "Long range", "Precise"], "limitations": ["Rare power cell", "Specialised training", "Overheats"]},
    {"tier": 10, "era": "Cosmic", "examples": ["Antimatter charge", "Dimensional blade", "Reality weapon"],
     "properties": ["Area/planetary effect", "Bypasses physical defences", "Reality-affecting"], "limitations": ["Extremely rare", "Catastrophic failure risk", "Draws cosmic-level attention"]},
]

TIER_BY_NUMBER = {t["tier"]: t for t in WEAPON_TIERS}
MAX_TIER = max(TIER_BY_NUMBER)

# Best-effort mapping from the existing WEAPON_TYPES catalog (see
# domain.characters.catalog.WEAPON_TYPES) to a default tier, so older
# characters and generated inventory items get a sensible weapon level
# without requiring every item to specify one explicitly.
_NAME_TIER_HINTS: list[tuple[tuple[str, ...], int]] = [
    # Most specific / setting-flavoured names first, so e.g. "Plasma Rifle"
    # matches the futuristic tier rather than the generic "rifle" tier.
    (("antimatter", "dimensional blade", "reality weapon", "reality-affecting"), 10),
    (("railgun", "monoblade", "cybernetic weapon"), 8),
    (("laser", "plasma", "energy blade", "phaser", "staff weapon", "zat'nik'tel", "bat'leth", "keyblade",
      "zanpakuto"), 9),
    (("smart weapon", "drone", "powered armour", "powered armor"), 7),
    (("gun", "rifle", "pistol"), 6),
    (("gunblade",), 6),
    (("crossbow",), 3),
    (("musket", "flintlock", "cannon"), 4),
    (("sword", "greatsword", "rapier", "katana", "scimitar", "bow", "longbow", "spear", "halberd", "trident",
      "javelin", "axe", "battleaxe", "hammer", "dagger", "whip", "flail", "scythe", "nunchaku", "tonfas",
      "shield", "claws", "gauntlets", "fists", "martial arts", "boxing", "kickboxing"), 2),
    (("magic weapon", "enchanted blade", "spirit weapon"), 3),
]


def tier_for_weapon_name(name: str) -> int:
    """Best-effort weapon tier for a free-text weapon/item name."""
    lowered = (name or "").lower()
    for keywords, tier in _NAME_TIER_HINTS:
        if any(k in lowered for k in keywords):
            return tier
    return 2  # default: mundane melee weapon


def describe_tier(tier: int) -> dict:
    tier = max(0, min(MAX_TIER, int(tier or 0)))
    return TIER_BY_NUMBER[tier]


def crossing_effect(item_tier: int, world_weapon_level: int) -> dict:
    """What happens when a weapon of `item_tier` is brought into a world whose
    weapon ceiling is `world_weapon_level`. A large gap either direction has
    narrative and mechanical consequences rather than a flat damage change."""
    item_tier = max(0, min(MAX_TIER, int(item_tier or 0)))
    world_weapon_level = max(0, min(MAX_TIER, int(world_weapon_level or 0)))
    gap = item_tier - world_weapon_level
    if gap <= 1:
        return {"status": "compatible", "gap": gap, "message": "Functions normally in this reality."}
    if gap <= 3:
        return {"status": "conspicuous", "gap": gap,
                "message": "Works, but is wildly out of place — expect suspicion, confiscation attempts, or a bounty on its origin."}
    if gap <= 5:
        return {"status": "unstable", "gap": gap,
                "message": "Anachronistic tech strains against local physics: reduced reliability, faster resource drain, occasional malfunction."}
    return {"status": "inert", "gap": gap,
            "message": "The gap is too large — the weapon's power source or principle doesn't function at all here."}
