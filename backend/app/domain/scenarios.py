"""New Game categories: the genre buckets offered on Play's start screen.

Each category maps onto legacy magic/tech/space tiers (for create_world) and
a reality type (see domain.multiverse). Two categories -- anime and game --
don't get their own prebuilt worlds; their scenario options are drawn from
the existing ANIME_PRESETS / GAME_PRESETS character catalogs instead, since
those already carry the right flavor (races, abilities, factions) for a
franchise-inspired starting point.
"""
from __future__ import annotations

CATEGORIES = [
    {"key": "fantasy", "label": "Fantasy", "magic": "high", "tech": "middle_age", "space": "fantasy", "reality_type": "Prime Reality"},
    {"key": "zombie", "label": "Zombie Apocalypse", "magic": "none", "tech": "modern", "space": "post-apocalyptic", "reality_type": "Dead Universe"},
    {"key": "supernatural", "label": "Supernatural", "magic": "medium", "tech": "modern", "space": "mystery", "reality_type": "Parallel Universe"},
    {"key": "mystery", "label": "Mystery", "magic": "low", "tech": "modern", "space": "mystery", "reality_type": "Prime Reality"},
    {"key": "drama", "label": "Drama", "magic": "none", "tech": "modern", "space": "drama", "reality_type": "Prime Reality"},
    {"key": "apocalyptic", "label": "Apocalyptic", "magic": "low", "tech": "post_collapse", "space": "post-apocalyptic", "reality_type": "Dead Universe"},
    {"key": "cyberpunk", "label": "Cyberpunk", "magic": "none", "tech": "cyberpunk", "space": "sci-fi", "reality_type": "Parallel Universe"},
    {"key": "alien_space", "label": "Alien Space", "magic": "none", "tech": "futuristic", "space": "sci-fi", "reality_type": "Alternate Reality"},
    {"key": "anime", "label": "Anime-Inspired", "magic": "high", "tech": "modern", "space": "fantasy", "reality_type": "Parallel Universe", "presets": "anime"},
    {"key": "game", "label": "Game-Inspired", "magic": "medium", "tech": "modern", "space": "fantasy", "reality_type": "Parallel Universe", "presets": "game"},
]

CATEGORY_BY_KEY = {c["key"]: c for c in CATEGORIES}


def category_defaults(key: str) -> dict:
    return CATEGORY_BY_KEY.get(key, CATEGORIES[0])
