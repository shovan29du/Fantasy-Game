"""World-scale ratings domain module."""
from backend.app.domain import worldscale


def test_axis_names_cover_all_eight_scales():
    assert set(worldscale.AXIS_NAMES) == {
        "science", "technology", "magic", "weapon", "power", "civilization", "danger", "horror",
    }


def test_clamp_bounds_to_0_10():
    assert worldscale.clamp(-5) == 0
    assert worldscale.clamp(15) == 10
    assert worldscale.clamp(7) == 7
    assert worldscale.clamp("not a number") == 0


def test_normalize_ratings_fills_missing_axes():
    ratings = worldscale.normalize_ratings({"magic": 9})
    assert ratings["magic"] == 9
    assert set(ratings.keys()) == set(worldscale.AXIS_NAMES)
    assert all(0 <= v <= 10 for v in ratings.values())


def test_default_ratings_from_tiers_fantasy_high_magic():
    ratings = worldscale.default_ratings_from_tiers("very_high", "middle_age", "fantasy")
    assert ratings["magic"] == 9
    assert ratings["technology"] == 2


def test_default_ratings_from_tiers_cyberpunk():
    ratings = worldscale.default_ratings_from_tiers("none", "futuristic", "sci-fi")
    assert ratings["magic"] == 0
    assert ratings["technology"] == 9


def test_axis_label_matches_value():
    assert worldscale.axis_label("magic", 0) == "Absent"
    assert worldscale.axis_label("weapon", 9) == "Futuristic"


def test_describe_world_contains_all_axes():
    text = worldscale.describe_world(worldscale.normalize_ratings({}))
    for axis in worldscale.AXIS_NAMES:
        assert axis.capitalize() in text
