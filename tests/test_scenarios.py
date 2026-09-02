"""New Game category/scenario domain module and prebuilt-world tagging."""
from backend.app.domain import scenarios
from backend.app.world.prebuilt import PREBUILT_WORLDS, get_prebuilt_by_category


def test_ten_categories_present():
    keys = {c["key"] for c in scenarios.CATEGORIES}
    assert keys == {
        "fantasy", "zombie", "supernatural", "mystery", "drama", "apocalyptic",
        "cyberpunk", "alien_space", "anime", "game",
    }


def test_anime_and_game_categories_use_presets():
    anime = scenarios.CATEGORY_BY_KEY["anime"]
    game = scenarios.CATEGORY_BY_KEY["game"]
    assert anime["presets"] == "anime"
    assert game["presets"] == "game"


def test_core_categories_have_no_presets_key():
    for key in ["fantasy", "zombie", "supernatural", "mystery", "drama", "apocalyptic", "cyberpunk", "alien_space"]:
        assert "presets" not in scenarios.CATEGORY_BY_KEY[key]


def test_category_defaults_fallback_for_unknown_key():
    assert scenarios.category_defaults("not-a-real-category") == scenarios.CATEGORIES[0]


def test_every_core_category_has_at_least_one_prebuilt_world():
    core_categories = [c["key"] for c in scenarios.CATEGORIES if "presets" not in c]
    for key in core_categories:
        assert get_prebuilt_by_category(key), f"No prebuilt world tagged for category {key!r}"


def test_prebuilt_categories_are_valid_or_none():
    valid = set(scenarios.CATEGORY_BY_KEY.keys()) | {None}
    for name, template in PREBUILT_WORLDS.items():
        assert template.get("category") in valid, f"{name} has an invalid category"


def test_create_prebuilt_world_applies_reality_type(temp_db):
    from backend.app.world import prebuilt

    world = prebuilt.create_prebuilt_world("Zombie Outbreak", reality_type="Dead Universe")
    assert world["reality_type"] == "Dead Universe"


def test_create_prebuilt_world_defaults_to_prime_reality(temp_db):
    from backend.app.world import prebuilt

    world = prebuilt.create_prebuilt_world("Haunted Precinct")
    assert world["reality_type"] == "Prime Reality"
