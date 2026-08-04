"""Character service boundary for catalog and persistence operations."""
from backend.app.domain.characters import get_library, random_backstory, random_goals, random_scenario
from core.auto_fill import auto_fill_character
from core.image_gen import generate_character_image
from core.storage import get_conn, now_iso

__all__ = [
    "auto_fill_character",
    "generate_character_image",
    "get_conn",
    "get_library",
    "now_iso",
    "random_backstory",
    "random_goals",
    "random_scenario",
]
