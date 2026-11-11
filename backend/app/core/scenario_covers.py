"""Scenario Cover Image Generation
Pre-generates and caches a cover image for every prebuilt scenario.
Images are saved to MEDIA_DIR/scenario_covers/<slug>.jpg and served at
/media/scenario_covers/<slug>.jpg so they persist across server restarts.

Style target: photorealistic, bright natural lighting, vibrant colors.
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

# Appended to every prompt for consistent bright-realistic look
_LIGHT = (
    ", golden hour sunlight, bright natural lighting, vivid colors, "
    "sharp focus, cinematic 8k photorealistic, ultra-detailed, no text, no watermark"
)

# ── Creative prompts keyed by exact scenario name ────────────────────────────
# Format: (scene_description, style)
# Style "Cinematic" → "cinematic scene, movie poster quality, dramatic lighting, 4k"
# Style "Realistic Portrait" → "photorealistic portrait photograph, studio lighting, 8k, detailed face"
# All prompts have _LIGHT appended at generation time.
SCENARIO_COVER_PROMPTS: dict[str, tuple[str, str]] = {
    "Ninja Village": (
        "A lone ninja warrior in full shinobi gear standing on a rooftop at sunrise, "
        "golden morning light catching the headband, misty mountain village below, "
        "kunai ready in hand, ancient wooden buildings with lanterns still glowing, "
        "cherry blossom petals drifting past, distant forest with signal fires fading",
        "Cinematic",
    ),
    "Magic Academy": (
        "A young student mage standing in a sunlit grand library hall of a gothic magic academy, "
        "towers of spell-books floating in amber light, stained-glass windows casting rainbow patterns "
        "on stone floors, magical runes glowing warm gold, wonder in their eyes, "
        "afternoon sun streaming through tall arched windows",
        "Cinematic",
    ),
    "Pirate Seas": (
        "A tall-ship pirate vessel sailing at dawn through tropical waters, "
        "golden sunrise lighting the billowing sails, jolly roger catching the breeze, "
        "crew silhouetted in warm light on the rigging, turquoise sea sparkling, "
        "distant island on the horizon, salt spray catching sunlight",
        "Cinematic",
    ),
    "Cyberpunk City": (
        "A skilled hacker in neon-lit cyberpunk alley at golden hour, "
        "holographic data streams glowing around gloved hands, chrome implants catching sunlight, "
        "vibrant neon reflections in rain puddles, futuristic cityscape in warm afternoon light, "
        "electric blue and orange hues, sharp high-tech details",
        "Cinematic",
    ),
    "Dragon Realm": (
        "A dragon rider soaring on a majestic golden dragon over mountain peaks at sunrise, "
        "brilliant morning light illuminating their bond, ancient peaks below, "
        "dragon scales catching warm gold and amber sunlight, clouds parting dramatically, "
        "other dragons visible as silhouettes in the bright sky",
        "Cinematic",
    ),
    "Hero Academy": (
        "A superhero student in a bright modern academy courtyard, "
        "unclassified power manifesting as brilliant white-gold light around their hands, "
        "classmates watching in sunlit uniform, wide blue sky above, "
        "academy buildings gleaming in strong afternoon sun, sense of potential and wonder",
        "Cinematic",
    ),
    "Medieval Kingdom": (
        "A knight errant on horseback at the edge of a sunlit medieval kingdom, "
        "golden morning light on cobblestone roads and stone walls, "
        "royal banners snapping in the breeze, distant castle towers catching the sun, "
        "green countryside stretching ahead, vivid blue sky with scattered clouds",
        "Cinematic",
    ),
    "The Wrongly Accused": (
        "A freed prisoner stepping into brilliant morning sunlight outside a stone fortress, "
        "squinting into radiant dawn light, shackle marks on wrists visible, "
        "loyal companion waiting with warm embrace at the gate, "
        "golden sunrise flooding the courtyard, tears catching the light",
        "Cinematic",
    ),
    "The Traitor's Escape": (
        "A cloaked princess and two ex-guards on horseback riding hard at dawn through misty countryside, "
        "first golden light breaking over hills, royal crest hidden under plain cloaks, "
        "horses' breath steaming in cool morning air, urgent determination on their faces, "
        "glowing sunrise ahead, pursuit torches fading behind",
        "Cinematic",
    ),
    "The Suitor's Tournament": (
        "A grand Renaissance tournament in full sunlight, armored knights on horseback, "
        "colorful pennants snapping in the breeze, golden afternoon light on the lists, "
        "princess watching from a flower-draped balcony in warm sunlight, "
        "crowd cheering, vivid heraldic colors, festive and bright",
        "Cinematic",
    ),
    "Blade for Hire": (
        "A battle-hardened mercenary standing guard on a mountain pass at sunrise, "
        "golden light on worn armor, cloaked figure of a princess visible behind, "
        "sweeping valley below in morning mist, sword at ready, "
        "dust catching sunlight from a distant road, vivid sky above",
        "Cinematic",
    ),
    "The Prince's Champion": (
        "A champion in gleaming armor at castle gates in bright morning sun, "
        "royal prince watching proudly from sunlit battlements, "
        "flags and banners brilliant in the light, "
        "childhood friend in distant colors silhouetted against bright sky, "
        "golden light across stone walls and cobblestones",
        "Cinematic",
    ),
    "Fifteen Years a Prisoner": (
        "A prisoner walking free from a medieval dungeon into radiant golden dawn, "
        "brilliant sunlight flooding the dark corridor behind them, "
        "overwhelmed by light after years inside, tears of relief, "
        "loyal figure waiting in the sun, sky impossibly blue and vast beyond the gate",
        "Cinematic",
    ),
    "Human and the Elven Queen": (
        "A human envoy and a luminous elven queen standing in a sunlit crystal hall of an ancient elven palace, "
        "warm golden light through tall tree-shaped windows, ancient forest visible outside, "
        "elven advisors in the background, a moment of unexpected connection, "
        "vibrant autumn leaves outside, warm amber and green hues",
        "Cinematic",
    ),
    "Ivywood Dormitory": (
        "A sunlit gothic university dormitory courtyard, ivy-covered walls glowing in afternoon light, "
        "a new student arriving with a scholarship letter, warm golden windows, "
        "other students glancing meaningfully from bright doorways, "
        "dappled light through tall trees, sense of mystery within warmth",
        "Cinematic",
    ),
    "Wandering Blades": (
        "An adventuring party of four at a bright forest clearing, "
        "dappled golden sunlight through tall trees, weapons at ease, "
        "mysterious merchant holding a second map, campfire glowing in warm afternoon light, "
        "vibrant green forest, ancient ruins visible through the trees",
        "Cinematic",
    ),
    "The Abandoned Party": (
        "A lone adventurer standing on a sunlit hilltop watching a distant celebration, "
        "warm golden afternoon light, determination in their posture, "
        "guild contract in hand, vivid blue sky, green hills rolling away, "
        "subtle strength of someone building something better alone",
        "Cinematic",
    ),
    "Space Station": (
        "A space station commander in a bright futuristic observation deck, "
        "brilliant Earth below filling the viewport, "
        "clean white station interior with warm accent lighting, "
        "holographic star charts glowing in the light, "
        "alien ambassador reflected in the window, vastness of lit space beyond",
        "Cinematic",
    ),
    "Demon Slayer Corps": (
        "A demon slayer in traditional Taisho-era Japan at golden sunrise, "
        "vibrant haori catching the morning breeze, wooden village behind, "
        "breathing technique visible as violet flame in warm sunlight, "
        "wisteria in bloom, golden rice fields, brilliant dawn sky",
        "Cinematic",
    ),
    "Post-Apocalypse": (
        "A vault dweller stepping out of an underground bunker into harsh bright sunlight, "
        "squinting at a golden wasteland stretching to the horizon, "
        "brilliant blue sky above ruined buildings, dust and light, "
        "vivid contrast of old-world color inside versus bleached bright world outside",
        "Cinematic",
    ),
    "Zombie Outbreak": (
        "Survivors on a rooftop in bright daylight, city below overrun, "
        "harsh afternoon sun on abandoned streets, signal mirror flashing, "
        "one survivor scanning the bright horizon with binoculars, "
        "vibrant blue sky contrasting with chaos below, sharp and vivid",
        "Cinematic",
    ),
    "Haunted Precinct": (
        "A detective in a sunlit precinct office, evidence board on a bright wall, "
        "afternoon light streaming through venetian blinds casting warm stripes, "
        "coffee steaming on the desk, old case photos and new leads, "
        "dust motes in the light, something just out of frame",
        "Cinematic",
    ),
    "Deep Space Frontier": (
        "A starship at the edge of a brilliantly lit nebula, "
        "vibrant purples, blues, and golds filling space, "
        "crew member at a bright viewport in wonder at first contact signal, "
        "alien colors saturating the view, light from two distant suns, vivid and luminous",
        "Cinematic",
    ),
    "Crown & Shadows": (
        "A grand Renaissance court in golden candlelight and afternoon sun through tall windows, "
        "nobles in vivid brocade and jewels, a document passing discreetly, "
        "gilded hall glowing warm, tapestries in deep color, "
        "sunlight and intrigue in equal measure",
        "Cinematic",
    ),
    "The Sterling Family": (
        "A bright modern manor living room, afternoon sun through large windows, "
        "family gathered in tense silence, one envelope on the coffee table, "
        "warm wood and clean lines, light flooding the room, "
        "family portraits on sunlit walls watching the scene",
        "Cinematic",
    ),
    "Office Rivalry": (
        "Two sharp professionals facing each other in a glass-walled boardroom, "
        "brilliant city skyline in golden afternoon sun behind them, "
        "light flooding the space, polished surfaces reflecting warmth, "
        "promotion document visible on a bright desk, everything professional and vivid",
        "Cinematic",
    ),
    "Twenty Years Gone": (
        "A person at the gate of a sunlit house on a bright autumn day, "
        "golden leaves, warm afternoon light on familiar walls, "
        "twenty years of absence visible in their posture, "
        "a figure in an upstairs window, vivid yellow and amber light everywhere",
        "Cinematic",
    ),
    "Blood & Loyalty": (
        "A crime family meeting in a bright warehouse in afternoon light, "
        "dust motes in golden sunbeams, loyalty maps on a brick wall, "
        "suited figures in strong directional light, sharp shadows, "
        "tension and honor facing each other in vivid clarity",
        "Cinematic",
    ),
    "Ridgewood University": (
        "Ridgewood University campus at golden autumn dusk, "
        "warm amber light on brick buildings, students on paths, "
        "a protagonist at a sunlit crossroads, old newspaper headline visible, "
        "vibrant orange and gold trees, blue sky, brightness and possibility",
        "Cinematic",
    ),
    "Second Marriage": (
        "A wedding venue in golden afternoon sunlight, "
        "two people at the altar in warm light, "
        "blended family in vivid attire, "
        "flowers brilliant in the light, sheer joy mixed with history, "
        "streaming sun through tall chapel windows",
        "Cinematic",
    ),
    "The Return": (
        "A traveler arriving on a bright main street in warm afternoon light, "
        "familiar storefronts in golden sun, duffel bag in hand, "
        "faces turning in recognition, vivid daylight, "
        "the gap between who they were and who they are visible in the light",
        "Cinematic",
    ),
    "The Forgotten Twin": (
        "Two identical faces in one bright photograph held in sunlit hands, "
        "one half in warm light, one half in cool shadow, "
        "family album spread on a sunlit table, "
        "afternoon light through lace curtains, golden and revealing",
        "Cinematic",
    ),
    "Before Everything Breaks": (
        "A couple at a bright apartment window in warm afternoon light, "
        "city outside vivid and golden, "
        "both looking different directions, "
        "a moment before honesty changes everything, "
        "warm light on faces, beautiful and tense",
        "Cinematic",
    ),
    "Lily at the Coffee Shop": (
        "A warm coffee shop on a bright autumn afternoon, "
        "golden light through fogged windows, two people at a counter, "
        "steam rising from cups in warm rays, "
        "autumn leaves outside catching the sun, "
        "cozy and luminous, the moment before something is said",
        "Cinematic",
    ),
    "The Ghost at the Wedding": (
        "A bright wedding reception, "
        "golden evening light on a dancing crowd, "
        "one person standing still in the warm glow spotting a face from the past, "
        "champagne catching the light, "
        "everyone else in vivid color and motion",
        "Cinematic",
    ),
    "Three Exes and a Waitress": (
        "A bright diner at noon, afternoon sun flooding in, "
        "familiar faces arriving one by one, "
        "a waitress refilling coffee in warm light, "
        "vintage diner in vivid color, humorous and warm, "
        "golden sunlight across checkered floors",
        "Cinematic",
    ),
    "Reese": (
        "Two people in a bright modern space, "
        "afternoon light streaming through floor-to-ceiling windows, "
        "a conversation that becomes something more, "
        "golden hour light on their faces, "
        "simple and luminous, genuine connection in vivid color",
        "Cinematic",
    ),
    "Audrey": (
        "A bright modern living room, afternoon sun warm through sheer curtains, "
        "two people close, one about to say something true, "
        "warm golden light on soft furnishings, "
        "emotional and luminous, honesty arriving in daylight",
        "Cinematic",
    ),
    "The Beach House": (
        "A beach house deck at golden sunset, "
        "warm orange light on the ocean and faces, "
        "old friends gathered for the last summer, "
        "sunlight on weathered wood and laughter, "
        "golden water, vivid sky, nostalgia made beautiful by light",
        "Cinematic",
    ),
    "Kendra": (
        "Two people walking in a bright city at golden hour, "
        "warm sunlight on modern streets, "
        "the city luminous around them, "
        "a moment of genuine connection in vivid daylight, "
        "long golden shadows, busy and beautiful",
        "Cinematic",
    ),
    "The Exiled Prince": (
        "A young man in plain clothes walking through a bright medieval market town, "
        "golden afternoon sunlight on stone streets, "
        "hood down just enough to show a noble face, "
        "colorful market stalls, vivid fabrics, a child recognizing him, "
        "distant palace towers gleaming in the sun",
        "Cinematic",
    ),
    "Elina Vos": (
        "A sharp professional woman in a bright glass-walled office at sunset, "
        "golden city light streaming in, "
        "the past and future visible in her expression, "
        "vibrant metropolis through the windows, "
        "warm light on a face about to make a decision",
        "Cinematic",
    ),
    "Megan at the Door": (
        "A bright front door at noon, strong daylight, "
        "one unexpected face in the golden light, "
        "a person at the threshold between who they were and who they are, "
        "suburban garden bright behind the visitor, "
        "warm and vivid, everything about to change",
        "Cinematic",
    ),
    "The Poison Bride": (
        "A medieval banquet hall at golden candlelight, "
        "a bride in luminous white at the head of a long table, "
        "warm flames catching jewels and silver, "
        "a goblet being lifted in bright torchlight, "
        "flowers brilliant in the warm light, "
        "beauty and danger in equal measure",
        "Cinematic",
    ),
    "Dragon Riders": (
        "A formation of dragon riders in brilliant sunrise light over mountain peaks, "
        "dragons in vivid colors catching first light, "
        "golden and orange sky, breath of fire illuminating the formation, "
        "majestic scale and beauty, luminous and epic",
        "Cinematic",
    ),
    "Witch Trials": (
        "A colonial village square at high noon, harsh bright sunlight, "
        "a woman in vivid dress standing before a crowd in strong daylight, "
        "real magic flickering like blue flame in bright light, "
        "accuser in the crowd, sky brilliant above the gathering, "
        "sharp and vivid, justice and injustice in full light",
        "Cinematic",
    ),
    "The Heist": (
        "A crew of specialists in a bright museum space at dawn, "
        "first light coming through skylights above precious art, "
        "laser grid visible in dusty morning air, "
        "golden exhibit lighting on a glass case, "
        "vivid oil paintings on the walls, tension in warm morning light",
        "Cinematic",
    ),
    "Fallen Kingdom": (
        "Ruins of a great throne room in bright afternoon sun streaming through broken walls, "
        "golden light on toppled pillars and scattered crown, "
        "a lone figure standing in the light, "
        "vibrant sky visible through the ruined ceiling, "
        "flowers growing through cracks in stone, life returning",
        "Cinematic",
    ),
    "The Oracle's Apprentice": (
        "A mystical mountain temple at sunrise, "
        "golden morning light flooding through open archways, "
        "apprentice kneeling before a glowing vision pool, "
        "warm amber light on stone and incense smoke, "
        "three paths of light in the vision, luminous and otherworldly",
        "Cinematic",
    ),
    "Shipwrecked": (
        "Shipwreck survivors on a beautiful tropical beach at golden morning, "
        "brilliant blue water, vivid green jungle, warm sun already high, "
        "ship wreckage catching morning light in the surf, "
        "paradise threatening and beautiful in equal measure",
        "Cinematic",
    ),
    "Vampire Court": (
        "An opulent court hall lit by hundreds of candles and daylight blocked by heavy drapes, "
        "warm amber light on centuries of gold and velvet, "
        "a human guest standing in a pool of light among shadows, "
        "rich jewel tones, vivid opulence, candle flames reflecting in dark eyes",
        "Cinematic",
    ),
    "The Wild Hunt": (
        "An ancient forest at golden twilight, shafts of amber light through tall oaks, "
        "spectral riders in warm mist, one mortal in a pool of golden light, "
        "magical boundary visible as shimmer in the last sunlight, "
        "vivid autumn leaves, luminous and haunting",
        "Cinematic",
    ),
    "Time Rift": (
        "A temporal rift blazing with golden-white light tearing through a bright modern city street, "
        "past and future visible in luminous layers, "
        "a figure standing in dazzling light at the threshold, "
        "brilliant light flooding the scene, vivid and overwhelming",
        "Cinematic",
    ),
    "Alien Contact": (
        "First contact on a sunlit research outpost, "
        "brilliant alien light pulsing in impossible geometry, "
        "scientist stepping forward in golden morning sun, "
        "vibrant aurora-like colors filling the sky, "
        "two forms of life in a pool of radiant shared light",
        "Cinematic",
    ),
    "Bounty Hunter": (
        "A lone bounty hunter on a bright frontier town main street at high noon, "
        "harsh sunlight on weathered leather and iron, "
        "wanted poster in hand, target visible through a bright saloon window, "
        "vivid blue sky, strong shadows, classic and sharp",
        "Cinematic",
    ),
    "The Last Mage": (
        "A mage in a sunlit cottage attic, "
        "afternoon light through dusty windows, "
        "power glowing warm gold in trembling hands, "
        "inquisitor soldiers visible in the bright street below, "
        "last spell-book in golden light, vivid and urgent",
        "Cinematic",
    ),
    "Rebellion": (
        "A resistance leader in a bright warehouse meeting room, "
        "afternoon light through high windows on a planning table, "
        "liberation maps, vivid faces in strong directional light, "
        "urgency and hope in equal measure, "
        "golden light on determined faces",
        "Cinematic",
    ),
    "Underground Arena": (
        "An underground arena lit by blazing torches and bright spotlights, "
        "fighter standing over an opponent in a ring of vivid orange flame and white light, "
        "roaring crowd in the warm bright haze, "
        "sweat and muscle in sharp relief, dramatic and luminous",
        "Cinematic",
    ),
    "The Forgotten God": (
        "Ancient jungle temple at golden noon, "
        "bright sunlight breaking through jungle canopy onto stone carvings coming alive, "
        "divine light emanating from the last believer's touch, "
        "vivid green jungle exploding with color in the light, "
        "gold and amber light on forgotten glyphs",
        "Cinematic",
    ),
    "Prison Break": (
        "A prison courtyard in bright daylight, "
        "one prisoner studying the layout in strong afternoon sun, "
        "light and shadow of walls and fences, "
        "a contact's signal catching sunlight from a distant rooftop, "
        "vivid and sharp, freedom visible in the bright sky above the walls",
        "Cinematic",
    ),
    "War Correspondent": (
        "A journalist at the edge of a golden ceasefire in warm afternoon sun, "
        "press badge in the light, notebook and camera in hand, "
        "two lines of soldiers visible in golden haze on either side, "
        "truth between them glowing in the warm light, vivid and human",
        "Cinematic",
    ),
    "Royal Scandal": (
        "A royal palace room flooded with morning light, "
        "courtiers in vivid dress frozen in strong sunlight, "
        "a document on the king's desk catching the light, "
        "gold and color everywhere, scandal and splendor in bright relief",
        "Cinematic",
    ),
    "The Cure": (
        "A scientist in a bright modern lab, "
        "afternoon sunlight on stainless steel and glass, "
        "a glowing flask on a sunlit counter, "
        "pharmaceutical agents visible through a bright window, "
        "hope and urgency in the light, vivid and clear",
        "Cinematic",
    ),
    "Galactic Senate": (
        "A vast alien senate chamber flooded with brilliant light from above, "
        "a human delegate in a pool of bright light at the center, "
        "hundreds of alien species in vivid colors on tiered seats, "
        "light beams crisscrossing the chamber, luminous and epic",
        "Cinematic",
    ),
    "The Cult": (
        "A compound at golden sunset, warm orange light on whitewashed walls, "
        "believers in pale robes moving in evening light, "
        "one person at the edge of the crowd in the last daylight, "
        "the leader's gaze finding them in the warm glow, vivid and unsettling",
        "Cinematic",
    ),
    "River Crossing": (
        "Two strangers at a bright riverbank in afternoon sun, "
        "golden light on rushing water, makeshift rope bridge, "
        "both soaked and vivid in strong daylight, "
        "trust forming in the light, lush green banks, "
        "blue sky and brilliant water",
        "Cinematic",
    ),
    "The Inheritance": (
        "A sunlit Victorian estate dining room, "
        "afternoon light through tall windows on a gathered family, "
        "a lawyer at the head of the table, one envelope in a pool of light, "
        "portraits on bright walls, vivid dress and expressions, warm and revealing",
        "Cinematic",
    ),
    "Island Survival": (
        "Survivors on a vivid tropical island beach at bright midday, "
        "brilliant sun, turquoise water, intense green jungle, "
        "signal fire smoke rising into blue sky, "
        "one person looking at the trees with something they haven't said yet, "
        "paradise and danger in full color",
        "Cinematic",
    ),
    "Cold Case": (
        "A detective in a bright office at noon, "
        "sunlight on a cold case evidence board, "
        "new photograph in strong afternoon light, "
        "twenty-year-old file in the glow, "
        "the moment a case breaks open in full vivid daylight",
        "Cinematic",
    ),
    "The Duel": (
        "Two duelists at dawn mist and golden light on an open field, "
        "brilliant sunrise behind them, seconds stepping back, "
        "dew on the grass catching the light, "
        "honor and consequence in the first golden rays, "
        "vivid morning colors, clear and final",
        "Cinematic",
    ),
    "Academy for Villains": (
        "A dark academy campus in strong afternoon sun, "
        "imposing Gothic architecture vivid against blue sky, "
        "students in black and deep colors in bright daylight, "
        "one student looking up at the sky with a question, "
        "sharp contrast of brilliant light and shadow",
        "Cinematic",
    ),
    "Midnight Market": (
        "A hidden night market illuminated by thousands of warm glowing lanterns, "
        "brilliant warm light on impossible goods, "
        "a dealer in a pool of golden lamp light, "
        "glowing contracts and vivid wares, "
        "magical luminosity, like a thousand suns in miniature",
        "Cinematic",
    ),
    "The Siege": (
        "Castle walls in vivid morning light, defenders in the sun, "
        "attackers below in bright open field, "
        "commander at the battlements in strong golden light, "
        "blue sky above, vivid banners, the fortress gleaming",
        "Cinematic",
    ),
    "Fae Bargain": (
        "A forest crossroads at golden dusk, "
        "warm amber light on a fae creature of living light and a mortal in the glow, "
        "glowing contracts rising like fireflies in the warm air, "
        "golden leaves, luminous mushroom rings, vivid and magical",
        "Cinematic",
    ),
    "Deep Jungle": (
        "An expedition team at the edge of ancient jungle ruins at high noon, "
        "brilliant tropical sun through the canopy, "
        "golden light on stone carvings emerging from green, "
        "vibrant jungle colors, the guide frozen at the treeline, "
        "light and shadow playing on something ancient",
        "Cinematic",
    ),
    "Haunted Circus": (
        "A traveling circus tent in golden late afternoon sun, "
        "warm amber light on colorful performers, "
        "one visitor in bright daylight noticing something that doesn't quite fit, "
        "vivid reds and yellows, the impossible visible in full light, "
        "beautiful and strange",
        "Cinematic",
    ),
    "The Healer": (
        "A healer in a bright field clinic between battle lines, "
        "golden afternoon sun on a makeshift tent, "
        "treating two opposing soldiers in warm light, "
        "vivid bandages and healing hands in the sun, "
        "compassion in full daylight, the war distant beyond the warmth",
        "Cinematic",
    ),
    "Underground Railroad": (
        "A conductor leading refugees through a bright autumn forest, "
        "golden afternoon light through tall trees, "
        "vivid fall colors, lamplight signals in distant farmhouse windows, "
        "urgency and hope in the golden day, "
        "light showing the path forward",
        "Cinematic",
    ),
    # ── Anime-Inspired ────────────────────────────────────────────────────────
    "Fairy Tail": (
        "A guild hall full of powerful mages celebrating after a victorious quest, "
        "golden afternoon sunlight flooding through tall arched windows, "
        "fire dragon slayer magic blazing warm orange, celestial spirits shimmering in the light, "
        "colorful guild mark banners glowing, laughter and camaraderie in vivid brightness",
        "Cinematic",
    ),
    "One Piece": (
        "A pirate crew standing triumphant on a tall-mast ship at brilliant sunrise, "
        "straw hat silhouetted against a burning orange sky over the Grand Line, "
        "devil fruit powers glowing in warm morning light, jolly roger snapping in the sea breeze, "
        "golden ocean stretching to the horizon, vibrant and epic",
        "Cinematic",
    ),
    "Naruto": (
        "A young shinobi on a rooftop at sunrise over a hidden leaf village, "
        "headband catching the first golden light, chakra swirling as brilliant blue energy, "
        "hokage mountain visible in warm morning mist, vibrant green forest behind, "
        "shadow clone jutsu signs in a pool of radiant dawn light",
        "Cinematic",
    ),
    "Bleach": (
        "A soul reaper in black shihakusho at the edge of Soul Society at golden dawn, "
        "zanpakuto drawn and glowing with brilliant spiritual pressure, "
        "hollow mask fragments catching warm light, vivid orange sky above the Seireitei, "
        "cherry blossoms drifting in golden morning air, luminous and intense",
        "Cinematic",
    ),
    "Dragon Ball": (
        "A Super Saiyan powering up on a rocky plateau at blazing noon, "
        "golden aura crackling with lightning against a vivid blue sky, "
        "ki energy radiating brilliant gold and white, rocks and dust swirling in the light, "
        "distant mountains in sharp golden haze, overwhelming power made luminous",
        "Cinematic",
    ),
    "Jujutsu Kaisen": (
        "A cursed energy user launching a Domain Expansion in a sunlit Tokyo street, "
        "brilliant blue-black cursed energy forming geometric patterns in afternoon light, "
        "Six Eyes glowing vivid purple, city buildings reflecting the supernatural light, "
        "ordinary sunlight and cursed power in vivid contrast, cinematic and intense",
        "Cinematic",
    ),
    "Demon Slayer": (
        "A demon slayer in vibrant haori charging through a bamboo forest at golden sunrise, "
        "breathing technique manifesting as vivid crimson and gold flame patterns, "
        "nichirin blade gleaming in strong morning light, wisteria blossoms catching sunlight, "
        "mist rising from golden rice paddies below, luminous and breathtaking",
        "Cinematic",
    ),
    "Soul Land": (
        "A powerful Spirit Master summoning twin spirits in a golden tournament arena, "
        "brilliant spirit rings orbiting in warm amber light, "
        "ancient Shrek Academy towers gleaming in afternoon sun behind them, "
        "spirit power blazing gold and silver, vivid and majestic",
        "Cinematic",
    ),
    "Hunter x Hunter": (
        "A hunter activating Nen in a sunlit forest clearing, "
        "golden aura crackling with focused nen energy, "
        "hunter license gleaming in bright afternoon light, "
        "vibrant green jungle around them, another hunter watching from the shadows, "
        "radiant and powerful, potential made visible in golden light",
        "Cinematic",
    ),
    # ── Game-Inspired ─────────────────────────────────────────────────────────
    "DC Comics": (
        "A caped hero landing in a sunlit Metropolis plaza, "
        "brilliant afternoon light on gleaming skyscrapers, "
        "cape catching the wind against vivid blue sky, "
        "golden emblem catching the sun, civilians below in bright daylight, "
        "vibrant primary colors, iconic and luminous",
        "Cinematic",
    ),
    "Marvel Comics": (
        "A team of superheroes assembled on a rooftop at golden hour, "
        "iron armor reflecting warm sunset light, thunder arc glowing, "
        "web-line catching brilliant afternoon sun, shield gleaming gold, "
        "vibrant city skyline behind them, heroic and luminous",
        "Cinematic",
    ),
    "Star Trek": (
        "A starship bridge crew at the helm as a vivid nebula fills the viewscreen, "
        "brilliant purples, blues and golds of deep space illuminating command uniforms, "
        "LCARS displays glowing in warm amber, captain standing at the center in strong light, "
        "sense of infinite possibility in the luminous deep space panorama",
        "Cinematic",
    ),
    "Stargate": (
        "An SG team stepping through the shimmering event horizon of a Stargate at golden dawn, "
        "brilliant blue-white wormhole light mixing with morning sunlight on alien ruins, "
        "ancient stone carvings in warm golden glow, desert plateau in vivid color below, "
        "radiant threshold between worlds, luminous and epic",
        "Cinematic",
    ),
    "Babylon 5": (
        "The great Babylon 5 space station gleaming in brilliant sunlight against stars, "
        "observation dome lit by warm interior light, alien ambassadors' ships docked alongside, "
        "Earth below glowing blue, vivid starfield backdrop, "
        "the last best hope for peace luminous against the darkness",
        "Cinematic",
    ),
    "Elder Scrolls": (
        "A Dragonborn standing atop the Throat of the World at golden dawn, "
        "Fus Ro Dah shout visible as blazing amber shockwave in morning light, "
        "Tamriel's landscape stretching below in vivid morning haze, "
        "dragon circling in brilliant sunrise sky, ancient Nordic ruins catching first light",
        "Cinematic",
    ),
    "Witcher": (
        "A witcher on horseback on a sunlit forest road through vivid autumn colors, "
        "silver sword catching bright afternoon light, cat-slit eyes scanning golden mist, "
        "witcher medallion glowing in warm sun, two swords on back in brilliant light, "
        "magical signs leaving warm traces in the golden air",
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
        base, style = SCENARIO_COVER_PROMPTS[scenario_name]
        return base + _LIGHT, style
    # Creative fallback from opening text
    genre_map = {
        "fantasy": "Fantasy Art", "anime": "Cinematic", "cyberpunk": "Cinematic",
        "supernatural": "Cinematic", "apocalyptic": "Cinematic", "zombie": "Cinematic",
        "mystery": "Cinematic", "drama": "Cinematic", "alien_space": "Cinematic",
    }
    style = genre_map.get(category, "Cinematic")
    excerpt = opening_text[:180].replace("\n", " ").strip() if opening_text else ""
    if excerpt:
        prompt = (
            f"Cinematic RPG scene for '{scenario_name}': {excerpt}"
            + _LIGHT
        )
    else:
        prompt = (
            f"{category or 'fantasy'} RPG scene, '{scenario_name}', "
            "cinematic illustration, atmospheric, detailed" + _LIGHT
        )
    return prompt, style


def generate_cover(scenario_name: str, opening_text: str = "", category: str = "",
                   force: bool = False) -> str | None:
    """Generate and save the cover image for one scenario.
    Returns the /media/… URL on success, None on failure.
    Skips generation if file already exists (unless force=True).
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
    total = len(scenarios)
    log.info("Scenario cover pre-generation started (%d scenarios, force=%s)", total, force)
    generated = 0
    for i, s in enumerate(scenarios):
        name = s.get("name", "")
        if not name:
            continue
        if not force and cover_path(name).exists():
            continue
        log.info("Generating cover %d/%d: %s", i + 1, total, name)
        url = generate_cover(
            name,
            opening_text=s.get("opening", ""),
            category=s.get("category", ""),
            force=force,
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
