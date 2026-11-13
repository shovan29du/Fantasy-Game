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


def test_every_link_points_at_a_real_entry_or_view():
    sections = {s["id"]: s for s in build_help()}
    ids = {sid: {e["id"] for e in s["entries"]} for sid, s in sections.items()}
    from backend.app.domain.help_content import _sections as raw_sections

    links = 0
    for section in raw_sections():
        for entry in section["entries"]:
            for label, target in entry["links"]:
                links += 1
                if target.startswith("view:"):
                    continue
                sec, _, name = target.partition("/")
                assert sec in sections, f"{section['id']}/{entry['name']}: unknown topic in link {target!r}"
                if name:
                    assert any(e["name"] == name for e in sections[sec]["entries"]), \
                        f"{section['id']}/{entry['name']}: link {target!r} has no such entry"
    assert links > 500


def test_entries_carry_stats_examples_and_links():
    entries = [e for s in build_help() for e in s["entries"]]
    assert sum(1 for e in entries if e["example"]) / len(entries) > 0.95
    assert sum(1 for e in entries if e["stats"]) / len(entries) > 0.8
    assert sum(1 for e in entries if e["links"]) / len(entries) > 0.95
    assert len({(s["id"], e["id"]) for s in build_help() for e in s["entries"]}) == len(entries)


def test_worked_examples_use_real_numbers():
    entries = {e["name"]: e for s in build_help() for e in s["entries"]}
    assert "55% chance" in entries["Attack rolls"]["example"]  # +5 against AC 15
    assert entries["Fireball"]["stats"]["Damage"].startswith("8d6")
    assert "8–48, average 28" in entries["Fireball"]["example"]
    assert entries["Goblin"]["stats"]["AC"] == 15
    assert "d10" in entries["Fighter"]["stats"]["Hit die"]


def test_every_topic_has_a_banner_and_pictures_have_unique_paths():
    from backend.app.domain.help_content import picture_specs

    specs = picture_specs()
    assert len({str(s["path"]) for s in specs}) == len(specs)
    banners = {s["id"] for s in specs if s["section"] == "sections"}
    assert banners == {s["id"] for s in build_help()}
    assert all(s["prompt"] and "no text" in s["prompt"] for s in specs)


def test_picture_endpoint_only_serves_defined_pictures():
    import pytest
    from fastapi import HTTPException
    from backend.app.main import HelpPictureIn, help_picture

    with pytest.raises(HTTPException) as err:
        help_picture(HelpPictureIn(section="spells", id="not-a-real-entry"))
    assert err.value.status_code == 404
