"""Weapon tier domain module."""
from backend.app.domain import weapons


def test_eleven_tiers_zero_through_ten():
    assert [t["tier"] for t in weapons.WEAPON_TIERS] == list(range(11))
    assert weapons.MAX_TIER == 10


def test_each_tier_has_examples_and_limitations():
    for tier in weapons.WEAPON_TIERS:
        assert tier["examples"]
        assert "era" in tier


def test_tier_for_weapon_name_matches_expected_era():
    assert weapons.tier_for_weapon_name("Sword") == 2
    assert weapons.tier_for_weapon_name("Crossbow") == 3
    assert weapons.tier_for_weapon_name("Rifle") == 6
    assert weapons.tier_for_weapon_name("Phaser") == 9
    assert weapons.tier_for_weapon_name("unknown gizmo") == 2


def test_tier_for_weapon_name_prefers_specific_futuristic_terms():
    # "Plasma Rifle" must land on the futuristic tier, not the generic
    # "rifle" tier, even though both keywords appear in the name.
    assert weapons.tier_for_weapon_name("Plasma Rifle") == 9
    assert weapons.tier_for_weapon_name("Laser gun") == 9
    assert weapons.tier_for_weapon_name("Railgun") == 8


def test_describe_tier_clamps_out_of_range():
    assert weapons.describe_tier(-3)["tier"] == 0
    assert weapons.describe_tier(999)["tier"] == 10


def test_crossing_effect_compatible_when_close():
    result = weapons.crossing_effect(item_tier=3, world_weapon_level=3)
    assert result["status"] == "compatible"


def test_crossing_effect_inert_when_gap_huge():
    result = weapons.crossing_effect(item_tier=9, world_weapon_level=1)
    assert result["status"] == "inert"
    assert result["gap"] == 8


def test_crossing_effect_conspicuous_and_unstable_bands():
    assert weapons.crossing_effect(4, 2)["status"] == "conspicuous"
    assert weapons.crossing_effect(7, 2)["status"] == "unstable"
