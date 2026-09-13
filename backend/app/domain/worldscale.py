"""World-scale ratings: eight 0-10 axes that describe a campaign reality.

Every world (prebuilt or player-created) carries a rating on each axis. The
axes drive what equipment, powers, and dangers make sense in that reality,
and are the basis for the multiverse "translation rules" applied when a
character crosses between worlds (see domain.multiverse).
"""
from __future__ import annotations

WORLD_AXES = {
    "science": "Understanding of medicine, physics, space, and biology.",
    "technology": "Tools, vehicles, computers, cybernetics, and infrastructure.",
    "magic": "Availability and strength of supernatural power.",
    "weapon": "Maximum normal weapon technology available (see weapon tiers).",
    "power": "Ceiling on personal power: ordinary, heroic, legendary, divine, cosmic.",
    "civilization": "Social organization: tribal through interstellar/multiversal.",
    "danger": "Severity of local threats, from mundane crime to reality-ending events.",
    "horror": "Tone, from heroic adventure through extreme survival horror.",
}

AXIS_NAMES = list(WORLD_AXES.keys())

# Short label for each 0-10 value, used for UI display (e.g. "Weapon 9 · Futuristic").
AXIS_LEVEL_LABELS = {
    "science": ["Superstition", "Folk remedy", "Pre-scientific", "Early scientific", "Classical", "Industrial",
                "Modern", "Advanced", "Post-human", "Transcendent", "Reality-altering"],
    "technology": ["None", "Stone tools", "Bronze/Iron age", "Medieval craft", "Early industrial", "Industrial",
                   "Digital", "Advanced digital", "Cybernetic", "Post-singularity", "Godlike"],
    "magic": ["Absent", "Folk superstition", "Rare relics", "Minor spellcraft", "Established spellcraft",
              "Common magic", "High magic", "Archmage-level", "Reality-bending", "World-shaping", "Cosmic/divine"],
    "weapon": ["Improvised", "Primitive", "Ancient", "Medieval", "Early firearms", "Industrial", "Modern",
               "Advanced modern", "Cyberpunk", "Futuristic", "Cosmic"],
    "power": ["Civilian", "Trained", "Competent", "Skilled", "Heroic", "Exceptional", "Superhuman", "Legendary",
              "Mythic", "Divine", "Cosmic"],
    "civilization": ["Ruins", "Nomadic/tribal", "Village", "City-state", "Kingdom", "Nation", "Industrial nation",
                      "Global", "Space-faring", "Interstellar", "Interstellar/multiversal"],
    "danger": ["Idyllic", "Safe", "Adventurous", "Risky", "Dangerous", "Hazardous", "Deadly", "Warzone",
               "Catastrophic", "Apocalyptic", "Reality-ending"],
    "horror": ["Lighthearted", "Adventurous", "Tense", "Grim", "Dark", "Disturbing", "Nightmarish", "Brutal",
               "Cosmic horror", "Extreme survival horror", "Unrelenting"],
}


def clamp(value: int) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = 0
    return max(0, min(10, value))


def axis_label(axis: str, value: int) -> str:
    labels = AXIS_LEVEL_LABELS.get(axis, [])
    value = clamp(value)
    return labels[value] if value < len(labels) else str(value)


def normalize_ratings(ratings: dict | None) -> dict:
    """Fill in any missing axis with a sane default (5) and clamp to 0-10."""
    ratings = ratings or {}
    return {axis: clamp(ratings.get(axis, 5)) for axis in AXIS_NAMES}


# Legacy string tiers ("medium", "middle_age", ...) used by the existing world
# creation form map onto sensible numeric defaults so old prebuilt worlds and
# the simple magic/tech dropdown still produce usable ratings.
_MAGIC_TIER_DEFAULTS = {
    "none": 0, "very_low": 1, "low": 3, "medium": 5, "high": 7, "very_high": 9, "cosmic": 10,
}
_TECH_TIER_DEFAULTS = {
    "ancient": 1, "primitive": 1, "middle_age": 2, "renaissance": 3, "age_of_sail": 3, "taisho_era": 4,
    "industrial": 5, "modern": 6, "futuristic": 9, "space_age": 9, "post_collapse": 2, "cyberpunk": 8,
}
_DANGER_BY_SETTING = {
    "post-apocalyptic": 8, "horror": 8, "apocalyptic": 9, "superhero": 5, "sci-fi": 5, "fantasy": 4, "drama": 1,
}
_HORROR_BY_SETTING = {
    "post-apocalyptic": 7, "horror": 9, "apocalyptic": 8,
}


def default_ratings_from_tiers(magic: str = "medium", tech: str = "middle_age", setting: str = "fantasy") -> dict:
    """Best-effort numeric ratings derived from the legacy string tiers, so
    every world (including the four prebuilt play realities and any world
    created via the simple dropdown form) gets a full set of 0-10 axes even
    if the caller never specifies them explicitly."""
    magic_v = _MAGIC_TIER_DEFAULTS.get((magic or "").lower(), 5)
    tech_v = _TECH_TIER_DEFAULTS.get((tech or "").lower(), 4)
    setting_key = (setting or "").lower()
    danger_v = _DANGER_BY_SETTING.get(setting_key, 4)
    horror_v = _HORROR_BY_SETTING.get(setting_key, 2)
    # Weapon ceiling roughly tracks technology, magic can push it further for
    # spellcraft-heavy worlds with otherwise low tech.
    weapon_v = clamp(max(tech_v, magic_v - 2))
    power_v = clamp(round((magic_v + tech_v) / 2))
    science_v = clamp(round(tech_v * 0.8))
    civilization_v = clamp(round((tech_v + 4) / 1.4))
    return normalize_ratings({
        "science": science_v, "technology": tech_v, "magic": magic_v, "weapon": weapon_v,
        "power": power_v, "civilization": civilization_v, "danger": danger_v, "horror": horror_v,
    })


def describe_world(ratings: dict) -> str:
    ratings = normalize_ratings(ratings)
    parts = [f"{axis.capitalize()} {ratings[axis]} ({axis_label(axis, ratings[axis])})" for axis in AXIS_NAMES]
    return " · ".join(parts)
