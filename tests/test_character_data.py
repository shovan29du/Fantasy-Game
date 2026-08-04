"""Backstory/scenario/goal template content requirements (core/character_data.py)."""
from core.character_data import random_backstory, random_scenario, random_goals
from backend.app.domain.characters.catalog import _BACKSTORIES, _SCENARIOS, _GOALS


def test_backstory_count_and_length():
    assert len(_BACKSTORIES) >= 50
    assert min(len(b.split()) for b in _BACKSTORIES) >= 100


def test_scenario_count_and_length():
    assert len(_SCENARIOS) >= 50
    assert min(len(s.split()) for s in _SCENARIOS) >= 100


def test_goal_count_and_length():
    assert len(_GOALS) >= 50
    assert min(len(g.split()) for g in _GOALS) >= 100


def test_random_backstory_fills_placeholders():
    text = random_backstory(race="Elf", profession="Blacksmith")
    assert "{race}" not in text
    assert "{profession}" not in text


def test_random_scenario_returns_from_list():
    assert random_scenario() in _SCENARIOS


def test_random_goals_fills_placeholder():
    text = random_goals(profession="Ranger")
    assert "{profession}" not in text
