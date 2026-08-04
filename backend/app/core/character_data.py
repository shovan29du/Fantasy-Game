"""Character catalog compatibility exports.

Canonical character data now lives under backend.app.domain.characters.
"""
from backend.app.domain.characters import catalog as _catalog
from backend.app.domain.characters.catalog import *  # noqa: F401,F403


def height_range_str(race):
    return _catalog.height_range_str(race)


def random_height(race):
    return _catalog.random_height(race)


def get_measurement_range(race, gender):
    return _catalog.get_measurement_range(race, gender)


def random_measurements(race, gender):
    return _catalog.random_measurements(race, gender)


def random_backstory(race="", profession=""):
    return _catalog.random_backstory(race, profession)


def random_scenario():
    return _catalog.random_scenario()


def random_goals(profession=""):
    return _catalog.random_goals(profession)


def _build_all():
    return _catalog._build_all()


def get_library():
    return _catalog.get_library()


def _build_lib():
    return _catalog._build_lib()


def generate_character_options_doc() -> str:
    return _catalog.generate_character_options_doc()
