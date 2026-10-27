"""SRD-derived spell list domain module."""
from backend.app.domain import spells


def test_spells_span_cantrip_through_level_five():
    assert spells.SPELL_LEVELS == [0, 1, 2, 3, 4, 5]


def test_every_spell_has_required_fields():
    required = {"level", "school", "classes", "casting_time", "range", "components", "duration",
                "effect_type", "description"}
    for name, spell in spells.SPELLS.items():
        missing = required - spell.keys()
        assert not missing, f"{name} is missing {missing}"
        assert spell["effect_type"] in ("attack", "save", "heal", "buff", "utility")


def test_attack_and_save_spells_carry_damage():
    for name, spell in spells.SPELLS.items():
        if spell["effect_type"] in ("attack", "save"):
            assert "damage" in spell, f"{name} should specify damage"


def test_heal_spells_carry_heal_dice():
    for name, spell in spells.SPELLS.items():
        if spell["effect_type"] == "heal":
            assert "heal" in spell, f"{name} should specify heal dice"


def test_iconic_srd_spells_present():
    for name in ["Fire Bolt", "Magic Missile", "Fireball", "Cure Wounds", "Shield", "Healing Word"]:
        assert name in spells.SPELLS


def test_spells_for_class_filters_by_profession():
    wizard_spells = spells.spells_for_class("Wizard")
    assert "Fireball" in wizard_spells
    assert all("Wizard" in spells.SPELLS[name]["classes"] for name in wizard_spells)


def test_spells_for_class_falls_back_to_full_list_for_unknown_profession():
    result = spells.spells_for_class("Farmer")
    assert set(result) == set(spells.SPELLS.keys())


def test_casting_ability_mapping():
    assert spells.casting_ability_for("Wizard") == "intelligence"
    assert spells.casting_ability_for("Priest") == "wisdom"
    assert spells.casting_ability_for("Bard") == "charisma_stat"
    assert spells.casting_ability_for("Farmer") == "intelligence"  # sensible default
