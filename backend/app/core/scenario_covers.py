"""Scenario Cover Image Generation
Pre-generates and caches a cover image for every prebuilt scenario.
Images are saved to MEDIA_DIR/scenario_covers/<slug>.jpg and served at
/media/scenario_covers/<slug>.jpg so they persist across server restarts.
"""
import re
import threading
import time
from pathlib import Path

from shared_config import MEDIA_DIR
from core.logging_setup import get_logger

log = get_logger(__name__)

COVERS_DIR = MEDIA_DIR / "scenario_covers"
COVERS_DIR.mkdir(parents=True, exist_ok=True)

# ── Creative prompts keyed by exact scenario name ────────────────────────────
# Each prompt is an evocative scene description tuned for that scenario's
# genre and backstory. Generic fallback is built from the category + name.
SCENARIO_COVER_PROMPTS: dict[str, tuple[str, str]] = {
    # (prompt, style)
    "Ninja Village": (
        "A lone ninja silhouetted against a blood-red moon atop a village rooftop, "
        "kunai drawn, hidden-leaf headband glinting, shadow clones dispersing in mist, "
        "dark forest beyond the gates, urgent warning fires on the northern border",
        "Anime Portrait",
    ),
    "Magic Academy": (
        "Grand gothic magic academy at twilight, a lone student standing in a corridor of "
        "floating spell-books and glowing runes, stained-glass windows casting multicolored "
        "light, mysterious power crackling at their fingertips, professors watching from shadows",
        "Fantasy Art",
    ),
    "Pirate Seas": (
        "A pirate ship cutting through storm-tossed seas at dawn, jolly roger snapping in the wind, "
        "Marines fleet visible on the horizon, golden treasure chest glowing below deck, "
        "crew scrambling on rigging, lightning splitting dark clouds above",
        "Fantasy Art",
    ),
    "Cyberpunk City": (
        "Neon-drenched cyberpunk alleyway, hacker jacked into a holographic data stream, "
        "corporate black-site guards reflected in puddles, encrypted data shards flying, "
        "neon signs in Japanese and English, rain hammering chrome implants",
        "Cyberpunk",
    ),
    "Dragon Realm": (
        "A young rider on a massive obsidian dragon soaring above ancient mountain peaks, "
        "fire-breathing dragonback corps in the sky behind them, shadow dragons emerging "
        "from storm clouds, dragon bond energy arcing between rider and dragon",
        "Fantasy Art",
    ),
    "Hero Academy": (
        "Superhero academy rooftop at golden hour, student with an unclassified crackling quirk "
        "standing apart from uniformed classmates, power manifesting as something the textbooks "
        "have no word for, principal watching from a tower window",
        "Fantasy Art",
    ),
    "Medieval Kingdom": (
        "A lone traveler clutching a royal knight's seal at the crossroads of a fog-shrouded "
        "medieval kingdom, cobblestone road stretching east into dark forest, royal banners "
        "behind them, something watching from the treeline ahead",
        "Fantasy Art",
    ),
    "The Wrongly Accused": (
        "A prisoner emerging from a stone dungeon into blinding dawn light, shackle marks on "
        "wrists, loyal spouse waiting at the gate with tears and secrets, the real culprit's "
        "shadow still visible inside the prison, stolen artifact glowing in the distance",
        "Dark Fantasy",
    ),
    "The Traitor's Escape": (
        "A rain-soaked princess and two ex-Royal Guards at a candlelit kitchen door at 3am, "
        "royal crest torn from their armor, urgent whispers, something hidden under a cloak, "
        "royal cavalry torches approaching down the moonlit road",
        "Dark Fantasy",
    ),
    "The Suitor's Tournament": (
        "Renaissance tournament grounds at sunset, armored suitors in the lists, a princess "
        "watching from a flower-draped balcony with carefully neutral expression, the herald "
        "smiling knowingly, foreign delegation murmuring in the shadows",
        "Fantasy Art",
    ),
    "Blade for Hire": (
        "A mercenary standing guard over a cloaked princess on a mountain road, usurper's "
        "cavalry dust rising in the valley below, classified documents clutched tight, "
        "three days from the capital, choice hanging in the air",
        "Dark Fantasy",
    ),
    "The Prince's Champion": (
        "A champion standing before castle gates, royal prince watching from the battlements, "
        "childhood friend-turned-warrior on the other side of the drawbridge in enemy colors, "
        "ancient title carved in stone above the arch, dawn breaking over besieged towers",
        "Fantasy Art",
    ),
    "Fifteen Years a Prisoner": (
        "A prisoner walking out of a stone dungeon after fifteen years, warden's shaking hands "
        "holding open the door, golden morning light flooding a cell that held a lifetime of "
        "injustice, the names of betrayers written on the wall behind",
        "Dark Fantasy",
    ),
    "Human and the Elven Queen": (
        "A human envoy and an ethereal elven queen facing each other across a crystal table in "
        "an ancient elven court, royal advisors horrified in the background, border map "
        "untouched between them, something unspoken written in both their eyes",
        "Fantasy Art",
    ),
    "Ivywood Dormitory": (
        "A half-empty gothic dormitory corridor at night, one lit room at the end, a student "
        "arriving with a scholarship letter in an atmosphere of meaningful glances and "
        "rearranged furniture, something unusual already stirring in the walls",
        "Dark Fantasy",
    ),
    "Wandering Blades": (
        "An adventuring party camped in an unmapped forest, campfire casting long shadows, "
        "a mysterious merchant holding a second set of documents, dungeon warden appearing "
        "from the treeline at dawn, the guild's map burning at the edges",
        "Fantasy Art",
    ),
    "The Abandoned Party": (
        "A lone adventurer watching from a hillside as former party members celebrate a "
        "victory built on stolen credit, face half in shadow, hands around a cold guild "
        "contract with their old companions' names on it, resolve in their eyes",
        "Dark Fantasy",
    ),
    "Space Station": (
        "A space station commander in an eerie corridor, sublevel four door sealed with "
        "warning glyphs, holographic logs of three missing captains floating in the air, "
        "alien ambassador watching from the airlock, AI core blinking in the darkness",
        "Sci-Fi",
    ),
    "Demon Slayer Corps": (
        "A demon slayer standing in mist at pre-dawn, unorthodox breathing style visible as "
        "violet flame, Hashira watching from the shadows, a crow motionless on a branch, "
        "top-secret mission scroll in hand, moonlit bamboo forest",
        "Dark Fantasy",
    ),
    "Post-Apocalypse": (
        "A vault dweller stepping out of a sealed bunker door for the first time, shielding "
        "eyes from harsh sunlight over a ruined city skyline, raider smoke on the horizon, "
        "settlement fires in the distance, the old world on faded wall maps behind them",
        "Dark Fantasy",
    ),
    "Zombie Outbreak": (
        "Survivor barricaded in a ruined building, zombie horde pressing against boarded windows, "
        "small group of survivors with dwindling supplies, a distant signal flare cutting "
        "through smoke-black sky, one person in the group hiding a bite mark",
        "Dark Fantasy",
    ),
    "Haunted Precinct": (
        "A detective in a rain-soaked precinct at midnight, crime board covered in impossible "
        "evidence, ghostly figure visible in the window reflection, cold case files bleeding "
        "ink, partner's chair empty, something in the evidence room moving",
        "Dark Fantasy",
    ),
    "Deep Space Frontier": (
        "A lone starship at the edge of charted space, alien signal pulsing on the console, "
        "first contact protocols ready, crew in tense silence, nebula of impossible colors "
        "outside the viewport, the unknown stretching infinitely ahead",
        "Sci-Fi",
    ),
    "Crown & Shadows": (
        "A Renaissance court at night, candlelit intrigue in velvet and steel, two noble "
        "houses scheming at opposite ends of a gilded banquet table, a document being passed "
        "in secret, throne casting a long shadow over everyone present",
        "Cinematic",
    ),
    "The Sterling Family": (
        "A tense family gathering in a modern manor, old secrets surfacing over inherited "
        "wealth, family portraits watching from the walls, one envelope on the dining table "
        "that changes everything, storm clouds gathering outside",
        "Cinematic",
    ),
    "Office Rivalry": (
        "Two professionals facing each other across a glass-walled boardroom, city skyline "
        "at dusk behind them, promotion document on the desk, the rest of the team "
        "watching through the glass, everything professional except the tension",
        "Cinematic",
    ),
    "Twenty Years Gone": (
        "A person standing outside the house they left twenty years ago, hand on the gate, "
        "memories layered like transparencies over the present, old photographs blending "
        "into the current street, a figure watching from an upstairs window",
        "Cinematic",
    ),
    "Blood & Loyalty": (
        "A crime family gathering at a rain-swept warehouse, loyalty tested by a single "
        "phone call, alliance maps pinned to concrete walls, two generations of "
        "obligations facing each other under a bare bulb",
        "Cinematic",
    ),
    "Ridgewood University": (
        "A sprawling university campus at autumn dusk, secrets buried under ivy and tradition, "
        "a student standing at a crossroads of two paths that lead to very different futures, "
        "old campus newspaper headline reflected in a dormitory window",
        "Cinematic",
    ),
    "Second Marriage": (
        "A wedding venue at golden hour, two people with histories standing at the altar, "
        "blended family watching with complicated expressions, fresh flowers over old scars, "
        "the question of whether this time it means something different",
        "Cinematic",
    ),
    "The Return": (
        "A person arriving back in the town they once left, duffel bag in hand, old memories "
        "overlaid on changed streets, familiar faces with unfamiliar expressions, "
        "the past and present colliding at the threshold of everything unfinished",
        "Cinematic",
    ),
    "The Forgotten Twin": (
        "Two faces, mirror images, one in shadow, one in light, a family secret splitting "
        "them down the middle, old photograph in a drawer half-burned, "
        "one twin building a life on a foundation the other never knew existed",
        "Cinematic",
    ),
    "Before Everything Breaks": (
        "A couple at a crossroads in a modern apartment, all the signs of a life built together "
        "and a conversation long overdue, city lights through the window, "
        "one moment before something irreversible is said",
        "Cinematic",
    ),
    "Lily at the Coffee Shop": (
        "A warm coffee shop in autumn rain, a barista and a regular at opposite sides of a counter "
        "that keeps shrinking, both holding back something they should probably just say, "
        "steam rising from two cups going cold",
        "Cinematic",
    ),
    "The Ghost at the Wedding": (
        "A wedding reception, everyone dancing, one person standing still at the edge of the room "
        "watching someone they were not supposed to see again, old feelings "
        "arriving uninvited with the plus-one that changes everything",
        "Cinematic",
    ),
    "Three Exes and a Waitress": (
        "A diner at closing time, three familiar faces from the past arriving one after another, "
        "a waitress who thought she had moved on refilling the same coffee cup, "
        "every table holding a different version of the same story",
        "Cinematic",
    ),
    "Reese": (
        "A quiet modern space between two people who keep ending up in the same place, "
        "afternoon light, a conversation that starts as one thing and becomes something else, "
        "one name that keeps coming up and one person who makes you rethink everything",
        "Cinematic",
    ),
    "Audrey": (
        "An intimate modern setting, two people, a secret kept longer than it should have been, "
        "the moment before honesty changes the shape of everything, warm light, "
        "close quarters, a truth arriving without warning",
        "Cinematic",
    ),
    "The Beach House": (
        "A beach house at the edge of summer, sun-faded photographs on the walls, "
        "old friends gathering for the last time, the sea indifferent, "
        "one conversation that cannot be postponed any longer",
        "Cinematic",
    ),
    "Kendra": (
        "A modern cityscape at night, two people whose paths keep crossing in ways "
        "that stopped feeling like coincidence, one honest moment arriving "
        "in an otherwise complicated series of choices",
        "Cinematic",
    ),
    "The Exiled Prince": (
        "A deposed prince traveling incognito through his own kingdom, hood drawn, "
        "royal crest hidden, allies and enemies everywhere in the market crowd, "
        "the palace spires visible and unreachable in the distance, "
        "a child who recognizes him even in disguise",
        "Dark Fantasy",
    ),
    "Elina Vos": (
        "A sharp professional in a modern city, one decision that sent her life "
        "in an unexpected direction, the past and the person she is becoming "
        "standing at opposite ends of a glass-walled office at dusk",
        "Cinematic",
    ),
    "Megan at the Door": (
        "A front door at night, one knock, one face no one expected, "
        "everything that was settled suddenly unsettled, "
        "two people standing in the light and dark of a threshold",
        "Cinematic",
    ),
    "The Poison Bride": (
        "A medieval banquet hall, a bride in white with a secret in her eyes, "
        "the groom reaching for a goblet, poison and politics woven into "
        "the wedding flowers, an alliance built on a lie about to unravel",
        "Dark Fantasy",
    ),
    "Dragon Riders": (
        "A formation of dragon riders soaring over ancient peaks at dawn, "
        "bond energy linking each rider to their dragon, an enemy formation "
        "emerging from storm clouds ahead, the last intact dragon wing "
        "standing between the kingdom and extinction",
        "Fantasy Art",
    ),
    "Witch Trials": (
        "A colonial-era village at dusk, accused witch standing before an angry crowd, "
        "real magic flickering at the edges of her hands, the accuser in the front row "
        "hiding something, storm clouds gathering over the town gallows",
        "Dark Fantasy",
    ),
    "The Heist": (
        "A crew of specialists in a darkened museum at 3am, laser grid visible in dusty air, "
        "the prize glowing in the case at the center of the room, "
        "one crew member's earpiece picking up something that was not in the plan",
        "Cinematic",
    ),
    "Fallen Kingdom": (
        "A once-great kingdom in ruins, a lone figure standing in the rubble of the throne room, "
        "crown half-buried in debris, loyal retainers forming a last guard, "
        "the conquering force's banners visible through shattered stained glass",
        "Dark Fantasy",
    ),
    "The Oracle's Apprentice": (
        "A mystical oracle's chamber at the edge of a cliff, apprentice kneeling before "
        "a vision pool showing three possible futures, the oracle's eyes already closed, "
        "a prophecy half-spoken hanging in the incense smoke",
        "Fantasy Art",
    ),
    "Shipwrecked": (
        "Survivors on a tropical island shore at dawn, ship wreckage in the surf, "
        "dense unknown jungle ahead, one among them with a secret about why the ship went down, "
        "first light revealing something in the treeline that should not be there",
        "Fantasy Art",
    ),
    "Vampire Court": (
        "An opulent vampire court at midnight, centuries of power arranged around a "
        "throne of onyx, a human standing in the center of it all with an invitation "
        "no one was supposed to extend, blood-red chandeliers above, "
        "ancient politics in every shadowed alcove",
        "Dark Fantasy",
    ),
    "The Wild Hunt": (
        "A moonlit ancient forest, the Wild Hunt thundering through the trees, "
        "spectral horses and riders in a rider's wake, one mortal who was not supposed "
        "to hear the horn but did, the boundary between worlds thinning with every step",
        "Dark Fantasy",
    ),
    "Time Rift": (
        "A temporal anomaly tearing through a modern city street, past and future bleeding "
        "into the present, a figure standing at the rift with the ability to close it "
        "or walk through it, every choice echoing in both directions",
        "Sci-Fi",
    ),
    "Alien Contact": (
        "First contact moment on a research outpost, an alien presence making itself known "
        "through light and impossible geometry, two species trying to understand each other "
        "across a gulf no translator was built for",
        "Sci-Fi",
    ),
    "Bounty Hunter": (
        "A lone bounty hunter on a dust-blown frontier, wanted poster in hand, "
        "target visible in the cantina window across the street, "
        "three other hunters closing in from different angles, "
        "one of them is not what they appear",
        "Fantasy Art",
    ),
    "The Last Mage": (
        "The last surviving mage in a world where magic is hunted, "
        "power barely contained behind trembling hands, inquisitors visible in the city below, "
        "the final spellbook hidden under floorboards, one decision that changes everything",
        "Dark Fantasy",
    ),
    "Rebellion": (
        "A resistance leader in an underground cell, liberation maps spread across a table, "
        "a regime informer's face on the board, the city above still sleeping, "
        "the moment a movement becomes a revolution",
        "Dark Fantasy",
    ),
    "Underground Arena": (
        "An underground fighting arena packed with roaring spectators, "
        "a fighter standing over a defeated opponent in a ring of torchlight, "
        "a shadowy patron in the VIP box who controls who wins and who disappears",
        "Dark Fantasy",
    ),
    "The Forgotten God": (
        "A crumbling temple in a jungle reclaimed by nature, carvings of a god "
        "no one worships anymore coming to life at the touch of the last believer, "
        "divine power awakening in the ruins, the old faith and the new world colliding",
        "Fantasy Art",
    ),
    "Prison Break": (
        "A maximum-security prison at night, one person with a plan that took three years, "
        "air vent diagram scratched into a floor tile, guards making their rounds, "
        "a contact on the outside blinking morse code from a flashlight",
        "Dark Fantasy",
    ),
    "War Correspondent": (
        "A journalist in a war zone at the golden hour of a brief ceasefire, "
        "notebook in one hand and camera in the other, standing between two armies "
        "and the story no one is supposed to tell, their press badge the only armor they have",
        "Cinematic",
    ),
    "Royal Scandal": (
        "A royal palace in uproar, compromising documents on the king's desk, "
        "courtiers frozen mid-bow at the revelation, the dynasty's future "
        "balanced on what happens in the next five minutes",
        "Fantasy Art",
    ),
    "The Cure": (
        "A scientist in a makeshift lab surrounded by specimen vials, the cure visible "
        "in a single glowing flask, pharmaceutical agents visible through the window, "
        "the choice between who gets to live and who controls the knowledge",
        "Sci-Fi",
    ),
    "Galactic Senate": (
        "An alien senate chamber of impossible architecture, a human delegate "
        "standing before a hundred species at a turning-point vote, "
        "the future of the galaxy hanging on a speech that must not fail",
        "Sci-Fi",
    ),
    "The Cult": (
        "An isolated compound at dusk, true believers going about evening rituals, "
        "one person who sees through the ceremony to something darker underneath, "
        "the leader's eyes finding them across the courtyard",
        "Dark Fantasy",
    ),
    "River Crossing": (
        "A flooded river crossing in a storm, two strangers who must trust each other "
        "to reach the other bank, what each is running from visible in what they carry, "
        "the bridge gone, the current rising",
        "Cinematic",
    ),
    "The Inheritance": (
        "A dusty Victorian estate at the reading of a will, estranged family gathered "
        "around a lawyer's table, one envelope addressed to someone no one expected, "
        "portraits of the deceased watching the living argue",
        "Cinematic",
    ),
    "Island Survival": (
        "A group of strangers on a lush but dangerous island, smoke from a makeshift signal "
        "fire, shelter half-built, one person who knows exactly how they all got here "
        "but hasn't said so yet, something moving in the jungle at night",
        "Fantasy Art",
    ),
    "Cold Case": (
        "A detective reopening a cold case file at midnight, evidence board with "
        "twenty-year-old photographs, a new lead that changes everything, "
        "the original detective's notes with something crossed out but still readable",
        "Dark Fantasy",
    ),
    "The Duel": (
        "Two duelists at dawn mist, seconds stepping back, "
        "the event that made this inevitable written in both their stances, "
        "the whole question of honor and pride and what it costs narrowed to one moment",
        "Fantasy Art",
    ),
    "Academy for Villains": (
        "A dark academy for those with villainous potential, students learning arts "
        "that heroes fear, one among them questioning who decided what counts as evil, "
        "the headmaster watching rankings as if they predict the future",
        "Dark Fantasy",
    ),
    "Midnight Market": (
        "A hidden market that only exists after midnight, impossible goods in impossible stalls, "
        "a dealer with a proposition that offers exactly what you want "
        "and something you are only beginning to understand you would have to give",
        "Dark Fantasy",
    ),
    "The Siege": (
        "A fortress under siege at nightfall, walls holding but barely, "
        "a defender who knows something the attackers do not, "
        "the commander choosing between survival and a secret that changes why the fortress matters",
        "Dark Fantasy",
    ),
    "Fae Bargain": (
        "A moonlit crossroads between worlds, a fae creature and a mortal "
        "negotiating terms that only one of them fully understands, "
        "glowing contracts written in living light, the fine print in a language "
        "no human was meant to read",
        "Fantasy Art",
    ),
    "Deep Jungle": (
        "An expedition deep in an uncharted jungle, ancient ruins emerging from the canopy, "
        "something old awakening at the explorers' approach, "
        "the guide stopping and refusing to go further, eyes on the treeline",
        "Fantasy Art",
    ),
    "Haunted Circus": (
        "A traveling circus at midnight, performers who are not entirely human, "
        "a tent that leads somewhere the tickets do not mention, "
        "one visitor who notices that the acts never end and the audience never leaves",
        "Dark Fantasy",
    ),
    "The Healer": (
        "A healer in a warzone between factions, treating both sides in a cellar clinic, "
        "the power to save anyone and the impossibility of choosing who, "
        "a secret in their healing gift that one faction would kill for",
        "Fantasy Art",
    ),
    "Underground Railroad": (
        "A network of safe houses in a historical setting, a conductor moving refugees "
        "through the night, lamplight signals in windows, an informant somewhere on the route, "
        "the next house two miles through dark forest",
        "Cinematic",
    ),
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def cover_path(scenario_name: str) -> Path:
    return COVERS_DIR / f"{_slugify(scenario_name)}.jpg"


def cover_url(scenario_name: str) -> str | None:
    p = cover_path(scenario_name)
    if p.exists():
        return f"/media/scenario_covers/{p.name}"
    return None


def _build_prompt(scenario_name: str, opening_text: str = "", category: str = "") -> tuple[str, str]:
    if scenario_name in SCENARIO_COVER_PROMPTS:
        return SCENARIO_COVER_PROMPTS[scenario_name]
    # Creative fallback: use opening text excerpt + genre
    genre_map = {
        "fantasy": "Fantasy Art", "anime": "Anime Portrait", "cyberpunk": "Cyberpunk",
        "supernatural": "Dark Fantasy", "apocalyptic": "Dark Fantasy", "zombie": "Dark Fantasy",
        "mystery": "Dark Fantasy", "drama": "Cinematic", "alien_space": "Sci-Fi",
    }
    style = genre_map.get(category, "Fantasy Art")
    excerpt = opening_text[:180].replace("\n", " ").strip() if opening_text else ""
    if excerpt:
        prompt = (
            f"Cinematic RPG scene for '{scenario_name}': {excerpt} — "
            "atmospheric illustration, dramatic lighting, detailed environment, no text"
        )
    else:
        prompt = (
            f"{category or 'fantasy'} RPG scene, '{scenario_name}', "
            "cinematic illustration, atmospheric lighting, epic composition, no text"
        )
    return prompt, style


def generate_cover(scenario_name: str, opening_text: str = "", category: str = "",
                   force: bool = False) -> str | None:
    """Generate and save the cover image for one scenario.
    Returns the /media/… URL on success, None on failure.
    Skips generation if the file already exists (unless force=True).
    """
    path = cover_path(scenario_name)
    if path.exists() and not force:
        return f"/media/scenario_covers/{path.name}"

    prompt_text, style = _build_prompt(scenario_name, opening_text, category)

    try:
        from core.image_gen import PHOTO_STYLES, download_image
        full_prompt = f"{PHOTO_STYLES.get(style, '')}, {prompt_text}" if style else prompt_text
        result_path = download_image(
            full_prompt, filename=str(path),
            width=512, height=384,
            providers=["pollinations", "comfyui", "automatic1111"],
        )
        if result_path and Path(result_path).exists():
            log.info("Generated scenario cover: %s → %s", scenario_name, result_path)
            return f"/media/scenario_covers/{path.name}"
    except Exception as exc:
        log.warning("Cover generation failed for %s: %s", scenario_name, exc)
    return None


def pregenerate_all_covers(scenarios: list[dict], force: bool = False) -> None:
    """Background thread: generate covers for every scenario that lacks one."""
    log.info("Scenario cover pre-generation started (%d scenarios)", len(scenarios))
    generated = 0
    for s in scenarios:
        name = s.get("name", "")
        if not name:
            continue
        if not force and cover_path(name).exists():
            continue
        url = generate_cover(
            name,
            opening_text=s.get("opening", ""),
            category=s.get("category", ""),
        )
        if url:
            generated += 1
        # Respect Pollinations rate limit (≥46 s between requests)
        time.sleep(47)
    log.info("Scenario cover pre-generation done: %d new images", generated)


def start_pregen_thread(scenarios: list[dict], force: bool = False) -> threading.Thread:
    t = threading.Thread(
        target=pregenerate_all_covers,
        args=(scenarios, force),
        daemon=True,
        name="scenario-cover-pregen",
    )
    t.start()
    return t


def all_covers_map() -> dict[str, str]:
    """Return {scenario_name: url} for every cover image that exists on disk."""
    result: dict[str, str] = {}
    for f in COVERS_DIR.iterdir():
        if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            result[f.stem] = f"/media/scenario_covers/{f.name}"
    return result
