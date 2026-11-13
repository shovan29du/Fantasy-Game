"""The Help reference must cover everything the game offers, so it is built
from the same data the game uses. These tests fail if something is left out."""
from backend.app.domain import dnd_weapons, spells
from backend.app.domain.characters import ALIGNMENTS, CHARACTER_TAGS, DND_RACES
from backend.app.domain.help_content import build_help
from core import levelling, quest_system, skill_tree_data, tactical_combat


def _sections():
    return {s["id"]: s for s in build_help()}


def _names(section):
    return {e["name"] for e in section["entries"]}


def _text(section):
    return " ".join(
        " ".join([e["name"], e["summary"], *e["fields"].keys(), *map(str, e["fields"].values())])
        for e in section["entries"]
    )


def test_sections_are_well_formed():
    sections = build_help()
    assert len({s["id"] for s in sections}) == len(sections)
    for section in sections:
        assert section["title"] and section["entries"]
        for entry in section["entries"]:
            assert entry["name"]
            assert entry["summary"] or entry["fields"], f"{section['id']}/{entry['name']} explains nothing"
            assert all(isinstance(v, (str, int, float)) for v in entry["fields"].values())


def test_every_race_feat_spell_and_skill_node_is_listed():
    s = _sections()
    assert set(DND_RACES) <= _names(s["races"])
    assert set(levelling.DND_FEATS) <= _names(s["feats"])
    assert set(spells.SPELLS) <= _names(s["spells"])
    assert {n["name"] for n in skill_tree_data.ALL_NODES.values()} <= _names(s["skilltree"])
    assert set(dnd_weapons.DND_WEAPONS) <= _names(s["equipment"])
    assert set(tactical_combat.DND_MONSTERS) <= _names(s["monsters"])


def test_every_class_tier_is_explained():
    text = _text(_sections()["classes"])
    for tier in levelling.PROFESSION_TIERS.values():
        for name in tier:
            assert name in text, f"class {name} missing from Help"


def test_every_tag_is_listed():
    text = _text(_sections()["tags"])
    assert [t for t in CHARACTER_TAGS if t not in text] == []


def test_alignments_quests_and_rules_are_covered():
    s = _sections()
    assert all(a in _text(s["character"]) for a in ALIGNMENTS)
    assert all(f"{q.title()} quest" in _names(s["quests"]) for q in quest_system.QUEST_TYPES)
    rules = _text(s["rules"])
    assert f"{levelling.xp_for_level(5):,} XP" in rules
    assert str(levelling.STAT_MAX) in rules


def test_help_states_the_content_limits():
    text = _text(_sections()["limits"]) + _text(_sections()["tags"])
    assert "minors" in text and "under 18" in text
