from pathlib import Path

from skill_loader import discover_skills, find_skill


def test_discovers_skill_and_parses_frontmatter(tmp_path):
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: A useful workflow\n---\n\n# Instructions\nDo the work.",
        encoding="utf-8",
    )
    skills = discover_skills(tmp_path)
    assert skills[0]["id"] == "skill:demo-skill"
    assert skills[0]["desc"] == "A useful workflow"
    assert skills[0]["prompt"].startswith("# Instructions")


def test_find_skill_does_not_escape_skill_root(tmp_path):
    assert find_skill("skill:../outside", tmp_path) is None


def test_bundled_skills_are_available():
    root = Path(__file__).parent / "skills"
    skills = discover_skills(root)
    assert len(skills) >= 20
    assert find_skill("skill:sn-deep-research", root)
