"""Multiverse domain module: reality types, power tiers, travel rules."""
from backend.app.domain import multiverse, worldscale


def test_reality_types_include_all_named_structures():
    expected = {
        "Prime Reality", "Alternate Reality", "Parallel Universe", "Mirror Universe",
        "Branching Timeline", "Pocket Dimension", "Dead Universe", "Merged Universe",
    }
    assert set(multiverse.REALITY_TYPES.keys()) == expected


def test_power_tiers_zero_through_eight():
    assert [t["tier"] for t in multiverse.POWER_TIERS] == list(range(9))
    assert multiverse.MAX_POWER_TIER == 8
    assert multiverse.POWER_TIER_BY_NUMBER[8]["name"] == "Multiversal"
    assert multiverse.POWER_TIER_BY_NUMBER[6]["name"] == "Divine"


def test_power_tier_for_level_scales_up():
    assert multiverse.power_tier_for_level(1) == 0
    assert multiverse.power_tier_for_level(5) == 2
    assert multiverse.power_tier_for_level(20) == 5


def test_generate_reality_signature_defaults_to_prime():
    sig = multiverse.generate_reality_signature("Aethoria Prime")
    assert sig["reality_type"] == "Prime Reality"
    assert sig["origin_world"] == "Aethoria Prime"
    assert "universe_tag" in sig and sig["universe_tag"]


def test_generate_reality_signature_rejects_unknown_type():
    sig = multiverse.generate_reality_signature("X", reality_type="Not A Real Type")
    assert sig["reality_type"] == "Prime Reality"


def test_generate_reality_signature_accepts_valid_type():
    sig = multiverse.generate_reality_signature("Earth-Z", reality_type="Mirror Universe")
    assert sig["reality_type"] == "Mirror Universe"


def test_travel_report_smooth_between_similar_worlds():
    ratings = worldscale.normalize_ratings({})
    report = multiverse.travel_report(ratings, ratings)
    assert report["effects"]
    assert "smooth" in report["effects"][0].lower()


def test_travel_report_flags_magic_instability_and_tech_gap():
    origin = worldscale.normalize_ratings({"magic": 9, "technology": 9})
    dest = worldscale.normalize_ratings({"magic": 0, "technology": 2})
    report = multiverse.travel_report(origin, dest)
    joined = " ".join(report["effects"]).lower()
    assert "magic does not function" in joined
    assert "hard to repair" in joined


def test_travel_report_mirror_universe_warning():
    ratings = worldscale.normalize_ratings({})
    report = multiverse.travel_report(ratings, ratings, dest_reality_type="Mirror Universe")
    assert any("reversed" in e.lower() or "loyalties" in e.lower() for e in report["effects"])


def test_travel_report_item_effects_use_weapon_tiers():
    ratings_low = worldscale.normalize_ratings({"weapon": 1})
    report = multiverse.travel_report(ratings_low, ratings_low, inventory_weapon_tiers=[9])
    assert report["item_effects"][0]["status"] in ("unstable", "inert")
