"""SRD-derived weapon list domain module."""
from backend.app.domain import dnd_weapons


def test_every_weapon_has_required_fields():
    required = {"category", "damage", "damage_type", "properties", "tier"}
    for name, weapon in dnd_weapons.DND_WEAPONS.items():
        missing = required - weapon.keys()
        assert not missing, f"{name} is missing {missing}"


def test_categories_cover_simple_and_martial_melee_and_ranged():
    assert dnd_weapons.WEAPON_CATEGORIES == sorted(
        {"Simple Melee", "Simple Ranged", "Martial Melee", "Martial Ranged"}
    )


def test_iconic_weapons_present():
    for name in ["Dagger", "Longsword", "Greatsword", "Longbow", "Shortbow", "Rapier"]:
        assert name in dnd_weapons.DND_WEAPONS


def test_finesse_and_ranged_detection():
    assert dnd_weapons.is_finesse_or_ranged("Rapier") is True  # finesse
    assert dnd_weapons.is_finesse_or_ranged("Longbow") is True  # ranged category
    assert dnd_weapons.is_finesse_or_ranged("Greataxe") is False
    assert dnd_weapons.is_finesse_or_ranged("Not A Weapon") is False


def test_weapon_tier_lookup_with_fallback():
    assert dnd_weapons.weapon_tier_for("Dagger") == 2
    assert dnd_weapons.weapon_tier_for("Greatsword") == 3
    assert dnd_weapons.weapon_tier_for("Nonexistent Weapon") == 2
