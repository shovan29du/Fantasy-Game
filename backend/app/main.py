"""FastAPI backend for the React AiChat Pro frontend."""
from __future__ import annotations

import json
import random
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.logging_setup import get_logger

log = get_logger(__name__)

# Minimum number of recent chat turns kept in the LLM context window, on top
# of the persistent memory facts pulled in separately (see memory_engine).
RECENT_HISTORY_MESSAGES = 30

import uuid

from backend.app.domain import dnd_weapons, multiverse, scenarios, spells as spells_domain, weapons, worldscale
from backend.app.domain.characters import (
    ALIGNMENTS,
    ALL_PRESET_SOURCES,
    ANIME_PRESETS,
    BODY_TYPES,
    CHARACTER_TAGS,
    DND_BACKGROUNDS,
    DND_RACES,
    EMOTION_STYLES,
    GAME_PRESETS,
    GENDERS,
    IMAGE_STYLES,
    MAGIC_TYPES,
    POWER_SYSTEMS,
    PROFESSIONS,
    QUIRKS_LIST,
    SKILLS_LIST,
    TRAITS_LIST,
    WEAPON_TYPES,
    random_backstory,
    random_goals,
    random_scenario,
)
from core.auto_fill import auto_fill_character
from core.character_search import fetch_character_card, search_characters
from backend.app.services.scenario_template_service import (
    delete_scenario_template,
    list_scenario_templates,
    render_template_scenario,
    save_scenario_template,
)
from backend.app.world.prebuilt import create_prebuilt_world, get_prebuilt_by_category, get_prebuilt_opening
from core import tactical_combat
from backend.app.chat_io.character_builder import build_characters_from_chat
from backend.app.chat_io.importer import import_chat_file, import_chat_url
from core.storage import get_conn, init_db, now_iso
from shared_config import MEDIA_DIR
from core.chat_engine import (
    build_system_prompt,
    clear_session,
    delete_message,
    edit_message,
    export_chat_html,
    export_chat_json,
    export_chat_txt,
    generate_suggestions,
    get_moments,
    get_history,
    save_message,
    search_messages,
    send_to_llm,
    tag_moment,
)
from core.image_gen import PHOTO_STYLES, download_image, generate_image_url
from core.knowledge_base import delete_document, index_file, index_folder, list_indexed, search_knowledge
from core.lorebook import create_entry, delete_entry, list_entries, toggle_entry
from core.levelling import (
    STAT_NAMES,
    add_feat_to_character,
    add_skill_to_character,
    add_spell_to_character,
    award_xp,
    get_full_sheet,
    increase_stat,
    xp_progress,
)
from core.media_pipeline import (
    ANIMATION_EFFECTS,
    create_animation,
    generate_animated_clip,
    generate_scene_video,
    get_provider_options,
    list_jobs,
    queue_media_job,
)
from core.memory_engine import MemoryEngine
from core.quest_system import (
    abandon_quest,
    complete_quest,
    generate_dynamic_quest,
    get_active_quests,
    get_quest_history,
    update_progress,
)
from core.relationship_engine import (
    ensure_relationship,
    get_event_history,
    get_relationship,
    list_all_relationships,
    record_interaction,
)
from core.storage import delete_character, delete_world, get_setting, set_setting
from core.world_engine import (
    add_law,
    advance_world_tick,
    create_faction,
    create_world,
    generate_dungeon,
    generate_npc,
    get_diplomacy,
    get_laws,
    get_locations,
    get_random_events,
    get_resources,
    get_timeline,
    get_weather_log,
    get_world,
    list_campaign_saves,
    list_dungeons,
    list_factions,
    list_npcs,
    list_worlds,
    save_campaign,
    set_diplomacy,
    simulate_combat,
)
from core.web_search import search_web
from backend.app.companion_studio.gpu_modules import router as companion_gpu_router

ROOT = Path(__file__).resolve().parents[2]
REACT_DIST = ROOT / "frontend" / "react_app" / "dist"

app = FastAPI(title="AiChat Pro API", version="1.0.0")
app.include_router(companion_gpu_router, prefix="/api/companion-studio")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
memory_engine = MemoryEngine()


class ScenarioTemplateIn(BaseModel):
    name: str
    scenario: str


class CharacterIn(BaseModel):
    name: str
    age: int = 25
    gender: str = ""
    race: str = ""
    alignment: str = "True Neutral"
    background: str = ""
    profession: str = ""
    scenario: str = ""
    backstory: str = ""
    goals: str = ""
    tags: list[str] = []
    skin: str = ""
    hair: str = ""
    eyes: str = ""
    body_type: str = ""
    height: str = ""
    bust_chest: str = ""
    waist: str = ""
    hips: str = ""
    looks: int = 5
    charisma_stat: int = 10
    strength: int = 10
    dexterity: int = 10
    intelligence: int = 10
    wisdom: int = 10
    constitution: int = 10
    speed: int = 10
    luck: int = 10
    weapon_training: list[str] = []
    magic_type: list[str] = []
    power_system: list[str] = []
    spells: list[str] = []
    skills: list[str] = []
    traits: list[str] = []
    quirks: list[str] = []
    emotion_styles: list[str] = []
    languages: list[str] = []
    level: int = 1
    xp: int = 0
    photo_path: str = ""
    identity_stability: int = 50
    origin_world: str = ""
    reality_type: str = "Prime Reality"
    power_tier: int | None = None
    origin: str = "Original fantasy world"
    secondary_ancestry: str = ""
    values_json: str = "{}"


class ChatMessageIn(BaseModel):
    role: str = "user"
    content: str
    session_id: str = "default"


class WorldIn(BaseModel):
    name: str
    magic: str = "medium"
    tech: str = "middle_age"
    space: str = "fantasy"
    num_locs: int = 8
    ratings: dict[str, int] | None = None
    reality_type: str = "Prime Reality"


class MultiverseTravelIn(BaseModel):
    origin_ratings: dict[str, int] | None = None
    dest_ratings: dict[str, int] | None = None
    origin_world_id: int | None = None
    dest_world_id: int | None = None
    dest_reality_type: str = "Prime Reality"
    character_id: int | None = None
    character_power_tier: int = 2


class SettingIn(BaseModel):
    key: str
    value: str


class MediaJobIn(BaseModel):
    job_type: str
    input_path: str = ""
    params: dict = {}


class ChatImportUrlIn(BaseModel):
    url: str


class ChatImportLoadIn(BaseModel):
    messages: list[dict]
    session_id: str = "imported"


class CharacterInferIn(BaseModel):
    messages: list[dict]
    scenario: str = ""
    main_character_name: str = ""


class CharacterImportIn(BaseModel):
    character: dict


class CharacterSearchIn(BaseModel):
    query: str = ""
    tags: list[str] = []
    nsfw: bool = True
    sort: str = "star_count"
    page: int = 1
    count: int = 20


class WebCharacterImportIn(BaseModel):
    result: dict


class GeneralWebSearchIn(BaseModel):
    query: str
    count: int = 10


class PhotoIn(BaseModel):
    character_id: int | None = None
    character: dict = {}
    style: str = "Anime Portrait"


class ChatSendIn(BaseModel):
    content: str
    session_id: str = "default"
    user_name: str = "User"
    user_sex: str = ""
    user_age: int | None = None
    character_id: int | None = None
    character_name: str = ""
    world_id: int | None = None
    participants: list[str] = []
    temperature: float = 0.7
    extra_context: str = ""


class ChatEditIn(BaseModel):
    content: str


class ChatSaveIn(BaseModel):
    session_id: str = "default"
    save_name: str
    character_name: str = ""
    world_id: int | None = None
    character_id: int | None = None


class ScenarioStartIn(BaseModel):
    category: str
    scenario_name: str = ""
    scenario_type: str = "prebuilt"  # prebuilt | preset | custom
    custom_text: str = ""


class QuestGenerateIn(BaseModel):
    character_name: str
    character_id: int | None = None
    world_id: int | None = None
    session_id: str = "default"


class QuestProgressIn(BaseModel):
    progress: int


class RelationshipIn(BaseModel):
    character_name: str
    sentiment: str = "neutral"
    note: str = ""


class XpIn(BaseModel):
    amount: int = 5
    reason: str = "chat"


class StatSpendIn(BaseModel):
    stat: str
    amount: int = 1


class SkillLearnIn(BaseModel):
    skill: str


class FeatLearnIn(BaseModel):
    feat: str


class SpellLearnIn(BaseModel):
    spell: str


class WeaponEquipIn(BaseModel):
    weapon_name: str
    equip_slot: str = "weapon"


class InventoryAddIn(BaseModel):
    item_name: str
    item_type: str = "misc"
    quantity: int = 1
    value: int = 0
    description: str = ""
    equip_slot: str = ""
    weapon_tier: int | None = None
    stat_bonuses: dict[str, int] = {}


class MemoryIn(BaseModel):
    fact: str
    source: str = "manual"
    memory_type: str = "episodic"
    character_name: str = ""
    importance: float = 0.7


class ImageIn(BaseModel):
    prompt: str
    style: str = ""
    width: int = 768
    height: int = 512
    save_to_chat: bool = True
    session_id: str = "default"


class AnimateIn(BaseModel):
    image_path: str
    effect: str = "ken_burns"
    duration: int = 5
    session_id: str = "default"


class TextToAnimationIn(BaseModel):
    prompt: str
    style: str = ""
    width: int = 768
    height: int = 512
    effect: str = "ken_burns"
    duration: int = 5
    save_to_chat: bool = True
    session_id: str = "default"


class TextToVideoIn(BaseModel):
    prompt: str = ""
    prompts: list[str] = []
    scenes: int = 3
    style: str = ""
    width: int = 768
    height: int = 512
    duration_per_slide: int = 3
    save_to_chat: bool = True
    session_id: str = "default"


class NpcIn(BaseModel):
    world_id: int
    name: str = ""
    profession: str = ""
    personality: str = ""


class FactionIn(BaseModel):
    world_id: int
    name: str
    alignment: str = "True Neutral"
    leader: str = ""
    territory: str = ""


class DiplomacyIn(BaseModel):
    world_id: int
    faction_a: str
    faction_b: str
    relation: str = "neutral"
    trade: bool = False
    treaty: str = ""


class DungeonIn(BaseModel):
    world_id: int | None = None
    name: str = ""
    dtype: str = "random"
    levels: int = 1
    rooms_per: int = 5


class CombatIn(BaseModel):
    attacker: dict = {"name": "Hero", "strength": 10}
    defender: dict = {"name": "Goblin", "constitution": 10}


class CombatStartIn(BaseModel):
    session_id: str = "default"
    world_id: int | None = None
    character_id: int | None = None


class CombatMoveIn(BaseModel):
    unit_id: int
    x: int
    y: int


class CombatTargetIn(BaseModel):
    unit_id: int
    target_id: int
    power_attack: bool = False


class CombatCastIn(BaseModel):
    unit_id: int
    spell_name: str
    target_id: int | None = None


class CombatUnitIn(BaseModel):
    unit_id: int


class CombatSpecialActionIn(BaseModel):
    unit_id: int
    action: str  # "dash" | "disengage" | "dodge" | "help"


class LawIn(BaseModel):
    name: str
    description: str = ""
    penalty: str = "Fine"


class CampaignSaveIn(BaseModel):
    save_name: str


class MediaItemIn(BaseModel):
    character_name: str = "Unassigned"
    media_type: str
    title: str
    file_path: str = ""
    description: str = ""
    tags: list[str] = []
    source: str = "manual"
    character_id: int | None = None


class AchievementIn(BaseModel):
    character_name: str = "Unassigned"
    title: str
    description: str = ""
    icon: str = "🏆"
    character_id: int | None = None


class MemorySnapshotIn(BaseModel):
    character_name: str = "Unassigned"
    title: str
    content: str = ""
    emotion: str = ""
    character_id: int | None = None


class LoreEntryIn(BaseModel):
    title: str
    content: str
    keywords: list[str] = []
    world_id: int = 0
    always_active: bool = False


class BoolSettingIn(BaseModel):
    key: str
    value: bool


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "app": "AiChat Pro"}


@app.get("/api/options")
def options() -> dict:
    return {
        "races": DND_RACES,
        "backgrounds": DND_BACKGROUNDS,
        "genders": GENDERS,
        "bodyTypes": BODY_TYPES,
        "professions": PROFESSIONS,
        "weaponTypes": WEAPON_TYPES,
        "magicTypes": MAGIC_TYPES,
        "powerSystems": POWER_SYSTEMS,
        "traits": TRAITS_LIST,
        "quirks": QUIRKS_LIST,
        "skills": SKILLS_LIST,
        "tags": CHARACTER_TAGS,
        "emotionStyles": EMOTION_STYLES,
        "alignments": ALIGNMENTS,
        "imageStyles": IMAGE_STYLES,
        "presetSources": ALL_PRESET_SOURCES,
        # Multiverse / character-origin expansion
        "origins": multiverse.CHARACTER_ORIGINS,
        "powerTiers": multiverse.POWER_TIERS,
        "realityTypes": multiverse.REALITY_TYPE_NAMES,
        "valuesAxes": multiverse.VALUES_AXES,
        # World-scale axes (8 × 0-10 ratings)
        "worldAxes": worldscale.WORLD_AXES,
        "worldAxisLabels": worldscale.AXIS_LEVEL_LABELS,
    }


@app.get("/api/random/prompts")
def random_prompts(race: str = "", profession: str = "") -> dict:
    return {
        "backstory": random_backstory(race, profession),
        "scenario": random_scenario(),
        "goals": random_goals(profession),
    }


@app.get("/api/characters")
def list_characters() -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM characters ORDER BY id DESC LIMIT 100").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@app.post("/api/characters")
def create_character(character: CharacterIn) -> dict:
    return {"id": _insert_character(character.model_dump()), "saved": True}


@app.post("/api/characters/import")
def import_character(payload: CharacterImportIn) -> dict:
    character = auto_fill_character(dict(payload.character))
    return {"id": _insert_character(character), "saved": True, "character": character}


@app.post("/api/characters/random")
def random_character() -> dict:
    import random

    race = random.choice(list(DND_RACES.keys()))
    gender = random.choice(GENDERS[:3])
    profession = random.choice(PROFESSIONS[:30])
    character = auto_fill_character(
        {
            "name": f"{random.choice(['Aldric','Lyra','Rowan','Nova','Kael','Seraphina','Quinn','Riven'])}_{random.randint(10,99)}",
            "race": race,
            "gender": gender,
            "profession": profession,
            "alignment": random.choice(ALIGNMENTS),
            "background": random.choice(DND_BACKGROUNDS[:-1]),
            "backstory": random_backstory(race, profession),
            "scenario": random_scenario(),
            "goals": random_goals(profession),
        }
    )
    return {"character": character}


@app.get("/api/characters/{character_id}/export")
def export_character(character_id: int) -> dict:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM characters WHERE id=?", (character_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Character not found.")
        data = dict(row)
        data.pop("id", None)
        return data
    finally:
        conn.close()


@app.post("/api/characters/photo")
def character_photo(payload: PhotoIn) -> dict:
    character = payload.character
    if payload.character_id:
        character = get_full_sheet(payload.character_id) or {}
    if not character:
        raise HTTPException(status_code=400, detail="Provide character_id or character data.")
    from core.image_gen import generate_character_image

    path = generate_character_image(character, style_key=payload.style)
    if payload.character_id and path:
        conn = get_conn()
        try:
            conn.execute("UPDATE characters SET photo_path=? WHERE id=?", (str(path), payload.character_id))
            conn.commit()
        finally:
            conn.close()
    return {"path": path}


@app.get("/api/explore/library")
def explore_library(query: str = "", race: str = "All", tags: str = "", limit: int = 50, page: int = 1) -> dict:
    from core.character_data import get_library

    library = get_library()
    wanted_tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
    filtered = library
    if query:
        q = query.lower()
        filtered = [c for c in filtered if q in c.get("name", "").lower() or q in c.get("race", "").lower() or q in c.get("profession", "").lower()]
    if wanted_tags:
        filtered = [c for c in filtered if any(tag in c.get("tags", []) for tag in wanted_tags)]
    if race and race != "All":
        filtered = [c for c in filtered if c.get("race", "") == race]
    start = max(0, page - 1) * limit
    return {"total": len(library), "filtered": len(filtered), "characters": filtered[start:start + limit]}


@app.post("/api/explore/library/import")
def import_library_character(payload: CharacterImportIn) -> dict:
    character = auto_fill_character(dict(payload.character))
    return {"id": _insert_character(character), "saved": True}


@app.post("/api/explore/library/import-all")
def import_library_characters(payload: dict) -> dict:
    count = 0
    for character in payload.get("characters", []):
        _insert_character(auto_fill_character(dict(character)))
        count += 1
    return {"imported": count}


@app.post("/api/explore/character-search")
def explore_character_search(payload: CharacterSearchIn) -> dict:
    results, error = search_characters(
        query=payload.query,
        tags=payload.tags,
        nsfw=payload.nsfw,
        sort=payload.sort,
        page=payload.page,
        count=payload.count,
    )
    return {"results": results, "error": error}


@app.post("/api/explore/character-search/import")
def import_web_character(payload: WebCharacterImportIn) -> dict:
    result = payload.result
    card = fetch_character_card(result.get("full_path", "")) if result.get("full_path") else None
    if card and (card.get("description") or card.get("personality")):
        character = {
            "name": card.get("name") or result.get("name", "Unknown"),
            "personality": card.get("personality", ""),
            "backstory": card.get("description") or result.get("tagline", ""),
            "scenario": card.get("scenario") or card.get("first_mes", ""),
            "tags": list(dict.fromkeys((card.get("tags") or []) + result.get("tags", []))),
        }
    else:
        character = {
            "name": result.get("name", "Unknown"),
            "backstory": result.get("tagline", ""),
            "tags": result.get("tags", []),
        }
    character = auto_fill_character(character)
    return {"id": _insert_character(character), "saved": True, "character": character, "full_card": bool(card)}


@app.post("/api/explore/web-search")
def explore_general_web_search(payload: GeneralWebSearchIn) -> dict:
    results, error = search_web(payload.query, count=payload.count)
    return {"results": results, "error": error}


def _insert_character(character: dict) -> int:
    reality_signature = multiverse.generate_reality_signature(
        character.get("origin_world") or character.get("scenario") or "",
        character.get("reality_type") or "Prime Reality",
    )
    power_tier = character.get("power_tier")
    if power_tier is None:
        power_tier = multiverse.power_tier_for_level(character.get("level", 1))
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            INSERT INTO characters
              (name,age,gender,race,alignment,background,personality,skin,hair,eyes,body_type,height,measurements,looks,
               charisma_stat,strength,dexterity,intelligence,wisdom,constitution,speed,luck,profession,weapon_training,
               magic_type,power_system,spells,skills,traits,backstory,scenario,goals,quirks,level,xp,photo_path,
               emotion_styles,identity_stability,reality_signature,power_tier,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                character.get("name", "Unknown"),
                character.get("age", 25),
                character.get("gender", ""),
                character.get("race", ""),
                character.get("alignment", "True Neutral"),
                character.get("background", ""),
                json.dumps(character.get("tags", [])) if isinstance(character.get("tags", []), list) else character.get("tags", "[]"),
                character.get("skin", ""),
                character.get("hair", ""),
                character.get("eyes", ""),
                character.get("body_type", ""),
                character.get("height", ""),
                json.dumps(
                    {
                        "bust_chest": character.get("bust_chest", ""),
                        "waist": character.get("waist", ""),
                        "hips": character.get("hips", ""),
                        "languages": character.get("languages", []),
                    }
                ),
                character.get("looks", 5),
                character.get("charisma_stat", 10),
                character.get("strength", 10),
                character.get("dexterity", 10),
                character.get("intelligence", 10),
                character.get("wisdom", 10),
                character.get("constitution", 10),
                character.get("speed", 10),
                character.get("luck", 10),
                character.get("profession", ""),
                json.dumps(character.get("weapon_training", [])),
                json.dumps(character.get("magic_type", [])),
                json.dumps(character.get("power_system", [])),
                json.dumps(character.get("spells", [])),
                json.dumps(character.get("skills", [])),
                json.dumps(character.get("traits", [])),
                character.get("backstory", ""),
                character.get("scenario", ""),
                character.get("goals", ""),
                json.dumps(character.get("quirks", [])),
                character.get("level", 1),
                character.get("xp", 0),
                character.get("photo_path", ""),
                json.dumps(character.get("emotion_styles", [])),
                character.get("identity_stability", 50),
                json.dumps(reality_signature),
                power_tier,
                now_iso(),
            ),
        )
        char_id = cur.lastrowid
        # Save fields added via schema migration (safe: columns exist after init_db).
        conn.execute(
            "UPDATE characters SET origin=?, secondary_ancestry=?, values_json=? WHERE id=?",
            (
                character.get("origin", "Original fantasy world"),
                character.get("secondary_ancestry", ""),
                character.get("values_json", "{}"),
                char_id,
            ),
        )
        conn.commit()
        return char_id
    finally:
        conn.close()


@app.get("/api/scenario-templates")
def scenario_templates() -> list[dict]:
    return list_scenario_templates()


@app.post("/api/scenario-templates")
def create_scenario_template(payload: ScenarioTemplateIn) -> dict:
    save_scenario_template(payload.name, payload.scenario)
    return {"saved": True}


@app.post("/api/scenario-templates/render")
def render_scenario_template(payload: ScenarioTemplateIn) -> dict:
    scenario, character_name = render_template_scenario(payload.scenario)
    return {"scenario": scenario, "characterName": character_name, "userName": "User"}


@app.delete("/api/scenario-templates/{template_id}")
def remove_scenario_template(template_id: int) -> dict:
    delete_scenario_template(template_id)
    return {"deleted": True}


@app.delete("/api/characters/{character_id}")
def remove_character(character_id: int) -> dict:
    return {"deleted": delete_character(character_id)}


@app.get("/api/chat/history")
def chat_history(session_id: str = "default", limit: int = 100) -> list[dict]:
    return get_history(session_id, limit)


@app.post("/api/chat/messages")
def create_chat_message(message: ChatMessageIn) -> dict:
    save_message(message.role, message.content, message.session_id)
    return {"saved": True}


@app.post("/api/chat/send")
def send_chat(payload: ChatSendIn) -> dict:
    character = get_full_sheet(payload.character_id) if payload.character_id else None
    character_name = payload.character_name or ((character or {}).get("name") if character else "Character")
    world = get_world(payload.world_id) if payload.world_id else None
    relationship = ensure_relationship(character_name) if character_name else None
    user_line = f"**{payload.user_name or 'User'}:** {payload.content}"
    save_message("user", user_line, payload.session_id)
    history = get_history(payload.session_id, limit=50)
    system_prompt = build_system_prompt(character=character, world=world, relationship=relationship, user_name=payload.user_name or "User")
    profile_bits = [payload.user_name or "User"]
    if payload.user_sex:
        profile_bits.append(payload.user_sex)
    if payload.user_age:
        profile_bits.append(f"age {payload.user_age}")
    system_prompt += f"\n[Player: {', '.join(profile_bits)}]"
    participants = payload.participants or ([character_name] if character_name else [])
    if len(participants) > 1:
        system_prompt += "\n[MULTI-PERSPECTIVE: Write responses for each character with their name prefix. Characters in scene: " + ", ".join(participants) + ".]"
    elif character_name:
        system_prompt += f"\n[Always prefix responses with **{character_name}:** to show who is speaking.]"
    quests = get_active_quests(character_name) if character_name else []
    if quests:
        system_prompt += "\n[Quests: " + "; ".join(q["title"][:30] for q in quests[:3]) + "]"
    try:
        from core.companion_soul import build_soul_prompt
        soul_context = build_soul_prompt(character_name)
        if soul_context:
            system_prompt += f"\n{soul_context}"
    except Exception:
        pass
    try:
        from core.lorebook import build_lorebook_context
        lore_context = build_lorebook_context(payload.content, payload.world_id or 0)
        if lore_context:
            system_prompt += f"\n{lore_context}"
    except Exception:
        pass
    if payload.extra_context:
        # Kept out of the saved message content so chat history stays clean
        # when reloaded -- this is prompt context only, not part of what the
        # player actually said.
        system_prompt += f"\n[Context: {payload.extra_context}]"
    messages = [{"role": "system", "content": system_prompt}]
    # Keep at least the last 30 turns in context so replies stay consistent
    # with recent events, on top of the persistent memory facts below.
    messages.extend({"role": msg["role"], "content": msg["content"]} for msg in history[-RECENT_HISTORY_MESSAGES:])
    try:
        memory_context = memory_engine.build_memory_context(query=payload.content, character_name=character_name)
        if memory_context:
            messages[-1]["content"] += f"\n[Memory: {memory_context}]"
    except Exception:
        pass
    try:
        response = send_to_llm(messages, temperature=payload.temperature)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}") from exc
    save_message("assistant", response, payload.session_id)
    if not response.startswith(("[LM Studio error]", "[Error]")):
        try:
            # Auto-accumulate memory from actual play so later replies stay
            # consistent even after the recent-message window scrolls past
            # this exchange -- build_memory_context() surfaces this back later.
            memory_engine.store_fact(
                f"{payload.user_name or 'Player'} said: {payload.content[:200]} | "
                f"{character_name or 'AI'} replied: {response[:200]}",
                source="auto", character_name=character_name or "",
            )
        except Exception:
            log.debug("Auto memory storage failed", exc_info=True)
    if character_name:
        sentiment = "positive" if any(word in payload.content.lower() for word in ["love", "kiss", "hug", "thank", "happy"]) else "neutral"
        if any(word in payload.content.lower() for word in ["hate", "attack", "kill", "angry"]):
            sentiment = "negative"
        if any(word in payload.content.lower() for word in ["flirt", "seduce", "intimate", "desire"]):
            sentiment = "flirt"
        record_interaction(character_name, sentiment, payload.content[:80])
        try:
            from core.companion_soul import update_affect
            update_affect(character_name, sentiment)
        except Exception:
            pass
    if payload.character_id:
        award_xp(payload.character_id, 5, "chat")
    _sync_world_from_text(payload.world_id, response)
    return {"reply": response, "session_id": payload.session_id}


@app.post("/api/chat/regen")
def regenerate_chat(payload: ChatSendIn) -> dict:
    last_user = payload.content
    if not last_user:
        for message in reversed(get_history(payload.session_id, limit=50)):
            if message.get("role") == "user":
                last_user = message.get("content", "")
                break
    payload.content = last_user
    payload.temperature = 0.95
    return send_chat(payload)


@app.delete("/api/chat/messages/{message_id}")
def remove_chat_message(message_id: int) -> dict:
    delete_message(message_id)
    return {"deleted": True}


@app.patch("/api/chat/messages/{message_id}")
def update_chat_message(message_id: int, payload: ChatEditIn) -> dict:
    edit_message(message_id, payload.content)
    return {"updated": True}


@app.post("/api/chat/messages/{message_id}/moment")
def mark_chat_moment(message_id: int) -> dict:
    tag_moment(message_id, True)
    return {"tagged": True}


@app.delete("/api/chat/messages/{message_id}/rewind")
def rewind_chat_to(message_id: int, session_id: str = "default") -> dict:
    """Delete every message after message_id in the session (keeps message_id itself)."""
    conn = get_conn()
    conn.execute("DELETE FROM messages WHERE id > ? AND session_id = ?", (message_id, session_id))
    conn.commit()
    conn.close()
    return {"rewound": True}


@app.post("/api/chat/messages/{message_id}/memory")
def save_message_to_memory(message_id: int) -> dict:
    """Save a chat message as a persistent memory fact."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM messages WHERE id=?", (message_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Message not found")
    fact = dict(row)["content"]
    memory_engine.store_fact(fact, source="chat-pin", memory_type="episodic", importance=0.9)
    return {"saved": True, "fact": fact[:120]}


@app.post("/api/chat/progressions")
async def chat_progressions(session_id: str = "default", context: str = "") -> dict:
    """Get 5 logical next-step options based on current chat context."""
    history = get_history(session_id, limit=10)
    last_ai = next((m['content'] for m in reversed(history) if m['role']=='assistant'), '')
    prompt_text = last_ai or context or "You are at the start of an adventure."
    try:
        raw = send_to_llm([
            {"role":"system","content":"You are a tabletop RPG narrator. Given the last story beat, generate exactly 5 short, distinct player action options (max 12 words each). Format: numbered list 1-5, one per line, no extra text."},
            {"role":"user","content":f"Last beat: {prompt_text[:400]}\nGenerate 5 options:"}
        ], temperature=0.85, max_tokens=200)
        lines = [l.strip() for l in raw.strip().split('\n') if l.strip() and l.strip()[0].isdigit()]
        options = [l.lstrip('0123456789.) ').strip() for l in lines][:5]
        if len(options)<3:
            options = ["Investigate the area","Talk to a nearby NPC","Check your inventory","Move to a new location","Wait and observe"]
    except Exception:
        options = ["Investigate the area","Talk to a nearby NPC","Check your inventory","Move to a new location","Wait and observe"]
    return {"options": options}


@app.post("/api/chat/alternatives")
async def chat_alternatives(session_id: str = "default", message_id: int = 0) -> dict:
    """Get 5 alternative outcomes for a given story moment."""
    history = get_history(session_id, limit=8)
    context = ' '.join(m['content'] for m in history[-3:])
    try:
        raw = send_to_llm([
            {"role":"system","content":"You are a tabletop RPG narrator. Given this story moment, generate 5 alternative story outcomes that could have happened differently (max 15 words each). Format: numbered list 1-5."},
            {"role":"user","content":f"Story context: {context[:500]}\nGenerate 5 alternative outcomes:"}
        ], temperature=0.9, max_tokens=250)
        lines = [l.strip() for l in raw.strip().split('\n') if l.strip() and l.strip()[0].isdigit()]
        options = [l.lstrip('0123456789.) ').strip() for l in lines][:5]
        if len(options)<3:
            options = ["A stranger intervenes","The enemy retreats","A portal opens nearby","A hidden passage reveals itself","An ally arrives at the last moment"]
    except Exception:
        options = ["A stranger intervenes","The enemy retreats","A portal opens nearby","A hidden passage reveals itself","An ally arrives at the last moment"]
    return {"options": options}


@app.delete("/api/chat/session/{session_id}")
def remove_chat_session(session_id: str) -> dict:
    clear_session(session_id)
    return {"cleared": True}


@app.get("/api/chat/search")
def chat_search(query: str, session_id: str = "default") -> list[dict]:
    return search_messages(query, session_id)


@app.get("/api/chat/suggestions")
def chat_suggestions(character_name: str = "the character") -> list[str]:
    return generate_suggestions(character_name)


@app.get("/api/chat/moments")
def chat_moments(session_id: str = "default") -> list[dict]:
    return get_moments(session_id)


@app.get("/api/chat/saves")
def chat_saves(limit: int = 25) -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM chat_saves WHERE save_name NOT LIKE '__auto%' ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@app.post("/api/chat/saves")
def create_chat_save(payload: ChatSaveIn) -> dict:
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO chat_saves (session_id, save_name, character_name, world_id, character_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (payload.session_id, payload.save_name, payload.character_name, payload.world_id, payload.character_id, now_iso()),
        )
        conn.commit()
        return {"saved": True}
    finally:
        conn.close()


@app.get("/api/scenarios/categories")
def scenario_categories() -> list[dict]:
    result = []
    for category in scenarios.CATEGORIES:
        entry = dict(category)
        if category.get("presets") == "anime":
            entry["scenarios"] = [{"type": "preset", "name": name} for name in ANIME_PRESETS]
        elif category.get("presets") == "game":
            entry["scenarios"] = [{"type": "preset", "name": name} for name in GAME_PRESETS]
        else:
            entry["scenarios"] = [{"type": "prebuilt", "name": name, "opening": get_prebuilt_opening(name)} for name in get_prebuilt_by_category(category["key"])]
        result.append(entry)
    return result


@app.post("/api/scenarios/start")
def start_scenario(payload: ScenarioStartIn) -> dict:
    defaults = scenarios.category_defaults(payload.category)
    session_id = f"game-{uuid.uuid4().hex[:12]}"
    if payload.scenario_type == "prebuilt" and payload.scenario_name:
        world = create_prebuilt_world(payload.scenario_name, reality_type=defaults["reality_type"])
        if world.get("error"):
            raise HTTPException(status_code=404, detail=world["error"])
    else:
        name = payload.scenario_name or f"{defaults['label']} Reality"
        world = create_world(name, defaults["magic"], defaults["tech"], defaults["space"], 8,
                              reality_type=defaults["reality_type"])
        if payload.scenario_type == "custom" and payload.custom_text.strip():
            create_entry("Opening Scenario", payload.custom_text.strip(), ["opening", "scenario"],
                          world_id=world["id"], always_active=True)
    return {"world": world, "session_id": session_id}


@app.get("/api/chat/export/{fmt}", response_class=PlainTextResponse)
def chat_export(fmt: str, session_id: str = "default", character_name: str = "") -> str:
    if fmt == "txt":
        return export_chat_txt(session_id)
    if fmt == "json":
        return export_chat_json(session_id, character_name)
    if fmt == "html":
        return export_chat_html(session_id)
    raise HTTPException(status_code=400, detail="Format must be txt, json, or html.")


@app.post("/api/chat/import/file")
async def import_chat_upload(file: UploadFile = File(...)) -> dict:
    suffix = Path(file.filename or "chat.txt").suffix.lower()
    if suffix not in {".txt", ".json", ".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail="Supported files: txt, json, pdf, docx.")
    import_dir = ROOT / "data" / "imports"
    import_dir.mkdir(parents=True, exist_ok=True)
    path = import_dir / f"{now_iso().replace(':', '-')}_{Path(file.filename or 'chat').name}"
    path.write_bytes(await file.read())
    messages = import_chat_file(str(path))
    return {"messages": messages, "count": len(messages), "path": str(path.relative_to(ROOT))}


@app.post("/api/chat/attach")
async def chat_attach_file(file: UploadFile = File(...)) -> dict:
    import zipfile, io as _io
    content = await file.read()
    fname = file.filename or "file"
    ext = Path(fname).suffix.lower()
    lines: list[str] = [f"📎 Attached file: {fname}"]
    if ext == ".zip":
        try:
            with zipfile.ZipFile(_io.BytesIO(content)) as zf:
                names = zf.namelist()
                lines.append(f"Contents ({len(names)} files):")
                for n in names[:40]:
                    lines.append(f"  • {n}")
                if len(names) > 40:
                    lines.append(f"  … and {len(names) - 40} more")
                # preview first readable text file
                for n in names:
                    if Path(n).suffix.lower() in {".txt", ".md", ".json", ".csv", ".py", ".js", ".ts"}:
                        try:
                            preview = zf.read(n).decode("utf-8", errors="replace")[:1500]
                            lines.append(f"\nPreview of {n}:\n{preview}")
                        except Exception:
                            pass
                        break
        except zipfile.BadZipFile:
            lines.append("(could not read zip)")
    elif ext in {".txt", ".md", ".csv", ".py", ".js", ".ts"}:
        lines.append(content.decode("utf-8", errors="replace")[:3000])
    elif ext == ".json":
        try:
            import json as _json
            parsed = _json.loads(content)
            lines.append(_json.dumps(parsed, indent=2)[:3000])
        except Exception:
            lines.append(content.decode("utf-8", errors="replace")[:3000])
    else:
        lines.append(f"({len(content):,} bytes — binary file, contents not shown)")
    summary = "\n".join(lines)
    return {"filename": fname, "summary": summary, "size": len(content)}


@app.get("/api/chat/export/zip")
async def export_session_zip(session_id: str = "default", character_name: str = "") -> StreamingResponse:
    import zipfile, io as _io
    buf = _io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("chat.txt", export_chat_txt(session_id))
        zf.writestr("chat.json", export_chat_json(session_id, character_name))
        zf.writestr("chat.html", export_chat_html(session_id))
    buf.seek(0)
    safe_sid = session_id[:12].replace("/", "-").replace("\\", "-")
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="worldweaver-{safe_sid}.zip"'},
    )


@app.post("/api/chat/import/url")
def import_chat_link(payload: ChatImportUrlIn) -> dict:
    messages = import_chat_url(payload.url)
    return {"messages": messages, "count": len(messages)}


@app.post("/api/chat/import/load")
def load_imported_chat(payload: ChatImportLoadIn) -> dict:
    saved = 0
    for message in payload.messages:
        speaker = str(message.get("speaker", "")).lower()
        role = "user" if speaker in {"user", "player", "me"} else "assistant"
        text = message.get("text") or message.get("content") or ""
        if text:
            save_message(role, f"**{message.get('speaker', role)}:** {text}", payload.session_id)
            saved += 1
    return {"saved": saved, "session_id": payload.session_id}


@app.post("/api/chat/import/infer-characters")
def infer_imported_characters(payload: CharacterInferIn) -> dict:
    characters = build_characters_from_chat(
        payload.messages,
        scenario=payload.scenario,
        main_character_name=payload.main_character_name,
    )
    return {"characters": characters, "count": len(characters)}


@app.get("/api/knowledge/documents")
def knowledge_documents() -> list[dict]:
    return list_indexed()


@app.get("/api/knowledge/search")
def knowledge_search(query: str, n: int = 5) -> list[dict]:
    return search_knowledge(query, n)


@app.post("/api/knowledge/index")
def knowledge_index() -> dict:
    count = index_folder()
    return {"indexed": count}


@app.post("/api/knowledge/index/file")
async def knowledge_index_file(file: UploadFile = File(...)) -> dict:
    knowledge_dir = ROOT / "knowledge" / "uploads"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    path = knowledge_dir / Path(file.filename or "document.txt").name
    path.write_bytes(await file.read())
    return {"indexed": index_file(str(path)), "path": str(path.relative_to(ROOT))}


@app.post("/api/knowledge/options-doc")
def knowledge_options_doc() -> dict:
    from core.character_data import generate_character_options_doc

    docs_dir = ROOT / "knowledge" / "generated"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "character_options.md"
    path.write_text(generate_character_options_doc(), encoding="utf-8")
    return {"indexed": index_file(str(path)), "path": str(path.relative_to(ROOT))}


@app.get("/api/knowledge/lorebook")
def lorebook_entries(world_id: int = 0) -> list[dict]:
    return list_entries(world_id)


@app.post("/api/knowledge/lorebook")
def create_lorebook_entry(payload: LoreEntryIn) -> dict:
    create_entry(
        payload.title,
        payload.content,
        payload.keywords,
        world_id=payload.world_id,
        always_active=payload.always_active,
    )
    return {"saved": True}


@app.delete("/api/knowledge/lorebook/{entry_id}")
def remove_lorebook_entry(entry_id: int) -> dict:
    delete_entry(entry_id)
    return {"deleted": True}


@app.post("/api/knowledge/lorebook/{entry_id}/toggle")
def toggle_lorebook_entry(entry_id: int, enabled: bool = True) -> dict:
    toggle_entry(entry_id, enabled)
    return {"updated": True}


@app.delete("/api/knowledge/documents/{document_id}")
def remove_knowledge_document(document_id: int) -> dict:
    delete_document(document_id)
    return {"deleted": True}


@app.get("/api/worlds")
def worlds() -> list[dict]:
    return list_worlds()


@app.post("/api/worlds")
def create_new_world(payload: WorldIn) -> dict:
    return create_world(payload.name, payload.magic, payload.tech, payload.space, payload.num_locs,
                         ratings=payload.ratings, reality_type=payload.reality_type)


@app.get("/api/worldscale/axes")
def worldscale_axes() -> dict:
    return {"axes": worldscale.WORLD_AXES, "levelLabels": worldscale.AXIS_LEVEL_LABELS}


@app.get("/api/weapons/tiers")
def weapon_tiers() -> list[dict]:
    return weapons.WEAPON_TIERS


@app.get("/api/multiverse/reality-types")
def multiverse_reality_types() -> dict:
    return multiverse.REALITY_TYPES


@app.get("/api/multiverse/power-tiers")
def multiverse_power_tiers() -> list[dict]:
    return multiverse.POWER_TIERS


@app.post("/api/multiverse/travel")
def multiverse_travel(payload: MultiverseTravelIn) -> dict:
    origin_ratings = payload.origin_ratings
    if origin_ratings is None and payload.origin_world_id is not None:
        origin_world = get_world(payload.origin_world_id)
        origin_ratings = origin_world["ratings"] if origin_world else None
    dest_ratings = payload.dest_ratings
    dest_reality_type = payload.dest_reality_type
    if dest_ratings is None and payload.dest_world_id is not None:
        dest_world = get_world(payload.dest_world_id)
        if dest_world:
            dest_ratings = dest_world["ratings"]
            dest_reality_type = dest_world.get("reality_type", dest_reality_type)
    if origin_ratings is None or dest_ratings is None:
        raise HTTPException(status_code=400, detail="Provide origin/dest ratings or world ids.")

    character_power_tier = payload.character_power_tier
    inventory_weapon_tiers: list[int] = []
    if payload.character_id is not None:
        sheet = get_full_sheet(payload.character_id)
        if sheet:
            character_power_tier = sheet.get("power_tier", character_power_tier) or character_power_tier
        conn = get_conn()
        try:
            rows = conn.execute(
                "SELECT item_name FROM inventory WHERE character_id=? AND equip_slot IS NOT NULL AND equip_slot != ''",
                (payload.character_id,)).fetchall()
        finally:
            conn.close()
        inventory_weapon_tiers = [weapons.tier_for_weapon_name(row["item_name"]) for row in rows]

    return multiverse.travel_report(origin_ratings, dest_ratings, dest_reality_type,
                                     character_power_tier, inventory_weapon_tiers)


@app.get("/api/worlds/{world_id}")
def world_detail(world_id: int) -> dict:
    world = get_world(world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found.")
    return world


@app.get("/api/worlds/{world_id}/locations")
def world_locations(world_id: int) -> list[dict]:
    return get_locations(world_id)


class LocationIn(BaseModel):
    name: str
    terrain: str = "Plains"
    loc_type: str = "area"
    description: str = ""
    x: float = 50.0
    y: float = 50.0

@app.post("/api/worlds/{world_id}/locations")
def add_world_location(world_id: int, loc: LocationIn):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO world_locations (world_id, name, loc_type, terrain, description, x, y) VALUES (?,?,?,?,?,?,?)",
        (world_id, loc.name, loc.loc_type, loc.terrain, loc.description, int(loc.x), int(loc.y))
    )
    conn.commit()
    row = conn.execute("SELECT * FROM world_locations WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@app.post("/api/worlds/{world_id}/tick")
def world_tick(world_id: int) -> dict:
    return advance_world_tick(world_id)


@app.get("/api/worlds/{world_id}/npcs")
def world_npcs(world_id: int) -> list[dict]:
    return list_npcs(world_id)


@app.post("/api/worlds/{world_id}/npcs")
def create_world_npc(world_id: int, payload: NpcIn | None = None) -> dict:
    custom = None
    if payload:
        custom = {k: v for k, v in payload.model_dump().items() if k != "world_id" and v}
    return generate_npc(world_id, custom)


@app.get("/api/worlds/{world_id}/factions")
def world_factions(world_id: int) -> list[dict]:
    return list_factions(world_id)


@app.post("/api/worlds/{world_id}/factions")
def create_world_faction(world_id: int, payload: FactionIn) -> dict:
    return create_faction(world_id, payload.name, payload.alignment, payload.leader, payload.territory)


@app.get("/api/worlds/{world_id}/dungeons")
def world_dungeons(world_id: int) -> list[dict]:
    return list_dungeons(world_id)


@app.post("/api/worlds/{world_id}/dungeons")
def create_world_dungeon(world_id: int, payload: DungeonIn) -> dict:
    return generate_dungeon(world_id, payload.name, payload.dtype, payload.levels, payload.rooms_per)


@app.post("/api/worlds/combat")
def world_combat(payload: CombatIn) -> dict:
    return simulate_combat(payload.attacker, payload.defender)


def _grant_combat_reward(character_id: int | None, world_id: int | None) -> dict:
    if not character_id:
        return {}
    xp_result = award_xp(character_id, 30, "combat victory")
    tier = 2
    if world_id:
        world = get_world(world_id)
        if world:
            tier = world.get("ratings", {}).get("weapon", 2)
    tier_info = weapons.describe_tier(tier)
    item_name = random.choice(tier_info["examples"])
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO inventory (character_id,item_name,item_type,quantity,value,description,equip_slot,stat_bonuses,source,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (character_id, item_name, "weapon", 1, 0, "Looted from a defeated foe.", None,
             json.dumps({"weapon_tier": tier}), "combat", now_iso()),
        )
        conn.commit()
    finally:
        conn.close()
    return {"xp_awarded": 30, "leveled_up": xp_result.get("levelled_up", False), "loot": item_name}


def _combat_response(result: dict, character_id: int | None = None, world_id: int | None = None) -> dict:
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    reward = {}
    if result.get("status") == "won":
        reward = _grant_combat_reward(character_id or result.get("character_id"), world_id or result.get("world_id"))
    return {**result, "reward": reward}


@app.post("/api/combat/start")
def combat_start(payload: CombatStartIn) -> dict:
    danger = 4
    if payload.world_id:
        world = get_world(payload.world_id)
        if world:
            danger = world.get("ratings", {}).get("danger", 4)
    result = tactical_combat.start_encounter(payload.session_id, payload.world_id, payload.character_id, danger)
    return _combat_response(result, payload.character_id, payload.world_id)


@app.get("/api/combat/active")
def combat_active(session_id: str = "default") -> dict:
    result = tactical_combat.get_active_encounter(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="No active encounter for this session.")
    return result


@app.get("/api/combat/{encounter_id}")
def combat_get(encounter_id: int) -> dict:
    result = tactical_combat.get_encounter(encounter_id)
    if not result:
        raise HTTPException(status_code=404, detail="Encounter not found.")
    return result


@app.post("/api/combat/{encounter_id}/move")
def combat_move(encounter_id: int, payload: CombatMoveIn) -> dict:
    result = tactical_combat.move_unit(encounter_id, payload.unit_id, payload.x, payload.y)
    return _combat_response(result, result.get("character_id"), result.get("world_id"))


@app.post("/api/combat/{encounter_id}/attack")
def combat_attack(encounter_id: int, payload: CombatTargetIn) -> dict:
    result = tactical_combat.attack_unit(encounter_id, payload.unit_id, payload.target_id, payload.power_attack)
    return _combat_response(result, result.get("character_id"), result.get("world_id"))


@app.post("/api/combat/{encounter_id}/cast")
def combat_cast(encounter_id: int, payload: CombatCastIn) -> dict:
    result = tactical_combat.cast_spell(encounter_id, payload.unit_id, payload.spell_name, payload.target_id)
    return _combat_response(result, result.get("character_id"), result.get("world_id"))


@app.post("/api/combat/{encounter_id}/end-turn")
def combat_end_turn(encounter_id: int, payload: CombatUnitIn) -> dict:
    result = tactical_combat.end_turn(encounter_id, payload.unit_id)
    return _combat_response(result, result.get("character_id"), result.get("world_id"))


@app.post("/api/combat/{encounter_id}/special-action")
def combat_special_action(encounter_id: int, payload: CombatSpecialActionIn) -> dict:
    result = tactical_combat.special_action(encounter_id, payload.unit_id, payload.action)
    return _combat_response(result, result.get("character_id"), result.get("world_id"))


@app.get("/api/worlds/{world_id}/resources")
def world_resources(world_id: int) -> list[dict]:
    return get_resources(world_id)


@app.get("/api/worlds/{world_id}/laws")
def world_laws(world_id: int) -> list[dict]:
    return get_laws(world_id)


@app.post("/api/worlds/{world_id}/laws")
def create_world_law(world_id: int, payload: LawIn) -> dict:
    add_law(world_id, payload.name, payload.description, payload.penalty)
    return {"saved": True}


@app.get("/api/worlds/{world_id}/diplomacy")
def world_diplomacy(world_id: int) -> list[dict]:
    return get_diplomacy(world_id)


@app.post("/api/worlds/{world_id}/diplomacy")
def create_world_diplomacy(world_id: int, payload: DiplomacyIn) -> dict:
    set_diplomacy(world_id, payload.faction_a, payload.faction_b, payload.relation, payload.trade, payload.treaty)
    return {"saved": True}


@app.get("/api/worlds/{world_id}/events")
def world_events(world_id: int, limit: int = 20) -> list[dict]:
    return get_random_events(world_id, limit)


@app.get("/api/worlds/{world_id}/timeline")
def world_timeline(world_id: int) -> list[dict]:
    return get_timeline(world_id)


@app.get("/api/worlds/{world_id}/weather")
def world_weather(world_id: int, limit: int = 20) -> list[dict]:
    return get_weather_log(world_id, limit)


@app.get("/api/worlds/{world_id}/saves")
def world_saves(world_id: int) -> list[dict]:
    return list_campaign_saves(world_id)


@app.post("/api/worlds/{world_id}/saves")
def create_world_save(world_id: int, payload: CampaignSaveIn) -> dict:
    return {"saved": save_campaign(world_id, payload.save_name)}


@app.delete("/api/worlds/{world_id}")
def remove_world(world_id: int) -> dict:
    return {"deleted": delete_world(world_id)}


@app.get("/api/media/providers")
def media_providers() -> list[dict]:
    return get_provider_options()


@app.get("/api/media/jobs")
def media_jobs(status: str = "", limit: int = 20) -> list[dict]:
    return list_jobs(status or None, limit)


@app.post("/api/media/jobs")
def create_media_job(payload: MediaJobIn) -> dict:
    return {"job_id": queue_media_job(payload.job_type, payload.input_path, payload.params)}


@app.get("/api/media/gallery")
def media_gallery(character_name: str = "", media_type: str = "", limit: int = 200) -> list[dict]:
    conn = get_conn()
    try:
        query = "SELECT * FROM media_items WHERE 1=1"
        args: list = []
        if character_name and character_name != "All":
            query += " AND character_name=?"
            args.append(character_name)
        if media_type:
            query += " AND media_type=?"
            args.append(media_type)
        query += " ORDER BY id DESC LIMIT ?"
        args.append(limit)
        return [dict(row) for row in conn.execute(query, args).fetchall()]
    finally:
        conn.close()


@app.post("/api/media/gallery")
def create_media_item(payload: MediaItemIn) -> dict:
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO media_items (character_id,character_name,media_type,title,description,file_path,tags,source,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (payload.character_id, payload.character_name, payload.media_type, payload.title, payload.description, payload.file_path, json.dumps(payload.tags), payload.source, now_iso()),
        )
        conn.commit()
        return {"id": cur.lastrowid, "saved": True}
    finally:
        conn.close()


@app.delete("/api/media/gallery/{media_id}")
def delete_media_item(media_id: int) -> dict:
    conn = get_conn()
    try:
        conn.execute("DELETE FROM media_items WHERE id=?", (media_id,))
        conn.commit()
        return {"deleted": True}
    finally:
        conn.close()


@app.get("/api/media/achievements")
def media_achievements(character_name: str = "") -> list[dict]:
    conn = get_conn()
    try:
        if character_name and character_name != "All":
            rows = conn.execute("SELECT * FROM achievements WHERE character_name=? ORDER BY id DESC", (character_name,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM achievements ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@app.post("/api/media/achievements")
def create_achievement(payload: AchievementIn) -> dict:
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO achievements (character_id,character_name,title,description,badge_icon,created_at) VALUES (?,?,?,?,?,?)",
            (payload.character_id, payload.character_name, payload.title, payload.description, payload.icon, now_iso()),
        )
        conn.commit()
        return {"id": cur.lastrowid, "saved": True}
    finally:
        conn.close()


@app.get("/api/media/memory-snapshots")
def media_memory_snapshots(character_name: str = "") -> list[dict]:
    conn = get_conn()
    try:
        if character_name and character_name != "All":
            rows = conn.execute("SELECT * FROM memory_snapshots WHERE character_name=? ORDER BY id DESC", (character_name,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM memory_snapshots ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@app.post("/api/media/memory-snapshots")
def create_memory_snapshot(payload: MemorySnapshotIn) -> dict:
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO memory_snapshots (character_id,character_name,title,content,emotion,created_at) VALUES (?,?,?,?,?,?)",
            (payload.character_id, payload.character_name, payload.title, payload.content, payload.emotion, now_iso()),
        )
        conn.commit()
        return {"id": cur.lastrowid, "saved": True}
    finally:
        conn.close()


@app.get("/api/relationships")
def relationships() -> list[dict]:
    return list_all_relationships()


@app.get("/api/relationships/{character_name}")
def relationship_detail(character_name: str) -> dict:
    return get_relationship(character_name) or ensure_relationship(character_name)


@app.get("/api/relationships/{character_name}/events")
def relationship_events(character_name: str, limit: int = 30) -> list[dict]:
    return get_event_history(character_name, limit)


@app.post("/api/relationships/interaction")
def relationship_interaction(payload: RelationshipIn) -> dict:
    return record_interaction(payload.character_name, payload.sentiment, payload.note)


@app.get("/api/quests/active")
def active_quests(character_name: str = "") -> list[dict]:
    return get_active_quests(character_name)


@app.get("/api/quests/history")
def quest_history(character_name: str = "", limit: int = 20) -> list[dict]:
    return get_quest_history(character_name, limit)


@app.post("/api/quests/generate")
def generate_story_quest(payload: QuestGenerateIn) -> dict:
    history = get_history(payload.session_id, limit=50)
    world = get_world(payload.world_id) if payload.world_id else None
    character = get_full_sheet(payload.character_id) if payload.character_id else None
    quest = generate_dynamic_quest(payload.character_name, history=history, world=world, character=character)
    if payload.character_id and quest:
        _add_quest_item(payload.character_id, quest)
    return {"quest": quest}


@app.post("/api/quests/{quest_id}/progress")
def progress_quest(quest_id: int, payload: QuestProgressIn) -> dict:
    update_progress(quest_id, payload.progress)
    return {"updated": True}


@app.post("/api/quests/{quest_id}/complete")
def finish_quest(quest_id: int, character_id: int | None = None) -> dict:
    complete_quest(quest_id)
    if character_id:
        award_xp(character_id, 50, "quest")
    return {"completed": True}


@app.delete("/api/quests/{quest_id}")
def remove_quest(quest_id: int) -> dict:
    abandon_quest(quest_id)
    return {"abandoned": True}


@app.get("/api/characters/{character_id}/sheet")
def character_sheet(character_id: int) -> dict:
    sheet = get_full_sheet(character_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Character not found.")
    xp = sheet.get("xp", 0) or 0
    _, into, need, fraction = xp_progress(xp)
    sheet["xp_progress"] = {"into": into, "need": need, "fraction": fraction}
    return sheet


@app.post("/api/characters/{character_id}/xp")
def add_character_xp(character_id: int, payload: XpIn) -> dict:
    award_xp(character_id, payload.amount, payload.reason)
    return {"sheet": get_full_sheet(character_id)}


@app.post("/api/characters/{character_id}/stats")
def spend_character_stat(character_id: int, payload: StatSpendIn) -> dict:
    if payload.stat not in STAT_NAMES:
        raise HTTPException(status_code=400, detail=f"Unknown stat. Use one of: {', '.join(STAT_NAMES)}")
    ok = increase_stat(character_id, payload.stat, payload.amount)
    return {"updated": ok, "sheet": get_full_sheet(character_id)}


@app.post("/api/characters/{character_id}/skills")
def learn_character_skill(character_id: int, payload: SkillLearnIn) -> dict:
    ok = add_skill_to_character(character_id, payload.skill)
    return {"updated": ok, "sheet": get_full_sheet(character_id)}


@app.post("/api/characters/{character_id}/feats")
def learn_character_feat(character_id: int, payload: FeatLearnIn) -> dict:
    ok = add_feat_to_character(character_id, payload.feat)
    return {"updated": ok, "sheet": get_full_sheet(character_id)}


@app.get("/api/spells")
def list_spells(profession: str | None = None) -> dict:
    names = spells_domain.spells_for_class(profession) if profession else list(spells_domain.SPELLS.keys())
    return {"spells": {name: spells_domain.SPELLS[name] for name in names}}


@app.post("/api/characters/{character_id}/spells")
def learn_character_spell(character_id: int, payload: SpellLearnIn) -> dict:
    if payload.spell not in spells_domain.SPELLS:
        raise HTTPException(status_code=400, detail="Unknown spell.")
    ok = add_spell_to_character(character_id, payload.spell)
    return {"updated": ok, "sheet": get_full_sheet(character_id)}


@app.get("/api/weapons/dnd")
def list_dnd_weapons() -> dict:
    return {"weapons": dnd_weapons.DND_WEAPONS, "categories": dnd_weapons.WEAPON_CATEGORIES}


@app.post("/api/characters/{character_id}/equip")
def equip_dnd_weapon(character_id: int, payload: WeaponEquipIn) -> dict:
    weapon = dnd_weapons.DND_WEAPONS.get(payload.weapon_name)
    if not weapon:
        raise HTTPException(status_code=400, detail="Unknown weapon.")
    conn = get_conn()
    try:
        conn.execute("UPDATE inventory SET equip_slot=NULL WHERE character_id=? AND equip_slot=?",
                     (character_id, payload.equip_slot))
        existing = conn.execute(
            "SELECT id FROM inventory WHERE character_id=? AND item_name=?", (character_id, payload.weapon_name)
        ).fetchone()
        stat_bonuses = json.dumps({"weapon_tier": weapon["tier"]})
        if existing:
            conn.execute("UPDATE inventory SET equip_slot=?, stat_bonuses=? WHERE id=?",
                         (payload.equip_slot, stat_bonuses, existing["id"]))
            item_id = existing["id"]
        else:
            cur = conn.execute(
                "INSERT INTO inventory (character_id,item_name,item_type,quantity,value,description,equip_slot,stat_bonuses,source,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (character_id, payload.weapon_name, weapon["category"], 1, 0,
                 f"{weapon['damage']} {weapon['damage_type']}", payload.equip_slot, stat_bonuses, "equip", now_iso()),
            )
            item_id = cur.lastrowid
        conn.commit()
        row = conn.execute("SELECT * FROM inventory WHERE id=?", (item_id,)).fetchone()
        return {"item": _item_with_weapon_tier(dict(row)), "sheet": get_full_sheet(character_id)}
    finally:
        conn.close()


def _item_with_weapon_tier(row: dict) -> dict:
    item = dict(row)
    try:
        bonuses = json.loads(item.get("stat_bonuses") or "{}")
    except Exception:
        bonuses = {}
    tier = bonuses.get("weapon_tier")
    item["weapon_tier"] = tier if tier is not None else weapons.tier_for_weapon_name(item.get("item_name", ""))
    item["weapon_tier_info"] = weapons.describe_tier(item["weapon_tier"])
    return item


@app.get("/api/characters/{character_id}/inventory")
def character_inventory(character_id: int) -> dict:
    conn = get_conn()
    try:
        items = conn.execute("SELECT * FROM inventory WHERE character_id=? ORDER BY item_type, item_name", (character_id,)).fetchall()
        economy = conn.execute("SELECT gold, credits, tokens FROM economy WHERE character_id=?", (character_id,)).fetchone()
        return {"economy": dict(economy) if economy else {"gold": 0, "credits": 0, "tokens": 0},
                "items": [_item_with_weapon_tier(row) for row in items]}
    finally:
        conn.close()


@app.post("/api/characters/{character_id}/inventory")
def add_inventory_item(character_id: int, payload: InventoryAddIn) -> dict:
    weapon_tier = payload.weapon_tier
    if weapon_tier is None and payload.item_type.lower() in ("weapon", "melee", "ranged"):
        weapon_tier = weapons.tier_for_weapon_name(payload.item_name)
    stat_bonuses = dict(payload.stat_bonuses)
    if weapon_tier is not None:
        stat_bonuses["weapon_tier"] = weapon_tier
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO inventory (character_id,item_name,item_type,quantity,value,description,equip_slot,stat_bonuses,source,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (character_id, payload.item_name, payload.item_type, payload.quantity, payload.value,
             payload.description, payload.equip_slot or None, json.dumps(stat_bonuses), "manual", now_iso()),
        )
        conn.commit()
        item_id = cur.lastrowid
        row = conn.execute("SELECT * FROM inventory WHERE id=?", (item_id,)).fetchone()
        return {"item": _item_with_weapon_tier(dict(row))}
    finally:
        conn.close()


@app.get("/api/memory/facts")
def memory_facts() -> dict:
    facts = memory_engine.get_all_facts()
    return {"facts": facts, "graph": memory_engine.get_graph_stats()}


@app.post("/api/memory/facts")
def create_memory_fact(payload: MemoryIn) -> dict:
    memory_engine.store_fact(
        payload.fact,
        payload.source,
        memory_type=payload.memory_type,
        character_name=payload.character_name,
        importance=payload.importance,
    )
    return {"saved": True}


@app.post("/api/memory/decay")
def decay_memory() -> dict:
    memory_engine.apply_decay()
    return {"applied": True}


@app.get("/api/media/image-styles")
def media_image_styles() -> list[str]:
    return list(PHOTO_STYLES.keys())


def _media_url(path: str) -> str:
    """Convert an absolute filesystem path under MEDIA_DIR into the relative
    URL the /media static mount serves it back out at. Empty string if the
    path is missing or falls outside MEDIA_DIR."""
    if not path:
        return ""
    try:
        return "/media/" + str(Path(path).relative_to(MEDIA_DIR)).replace("\\", "/")
    except ValueError:
        return ""


@app.post("/api/media/image")
def create_image(payload: ImageIn) -> dict:
    prompt = f"{PHOTO_STYLES.get(payload.style, '')}, {payload.prompt}" if payload.style else payload.prompt
    # Skip placeholder provider so that if server-side download fails we fall
    # back to the direct Pollinations URL that the user's browser can load.
    path = download_image(prompt, width=payload.width, height=payload.height,
                          providers=["pollinations", "comfyui", "automatic1111"])
    url = _media_url(path) or generate_image_url(prompt, payload.width, payload.height)
    if payload.save_to_chat:
        save_message("assistant", f"🖼️ *[{payload.prompt[:80]}]*", payload.session_id)
    return {"path": path, "url": url, "prompt": prompt}


@app.get("/api/media/animation-effects")
def media_animation_effects() -> list[str]:
    return list(ANIMATION_EFFECTS.keys())


@app.post("/api/media/animate")
def animate_image(payload: AnimateIn) -> dict:
    output = create_animation(payload.image_path, effect=payload.effect, duration=payload.duration)
    if output:
        save_message("assistant", f"🎞️ *[Animated: {payload.effect}, {payload.duration}s]*", payload.session_id)
    return {"path": output, "url": _media_url(output)}


@app.post("/api/media/text-to-animation")
def text_to_animation(payload: TextToAnimationIn) -> dict:
    result = generate_animated_clip(payload.prompt, style_prefix=PHOTO_STYLES.get(payload.style, ""),
                                     width=payload.width, height=payload.height,
                                     effect=payload.effect, duration=payload.duration)
    if not result:
        raise HTTPException(status_code=502, detail="Could not render an animation (image generation or ffmpeg failed).")
    if payload.save_to_chat:
        save_message("assistant", f"🎬 *[Animated: {payload.prompt[:80]}]*", payload.session_id)
    return {
        "image_path": result["image_path"], "image_url": _media_url(result["image_path"]),
        "video_path": result["video_path"], "video_url": _media_url(result["video_path"]),
    }


@app.post("/api/media/text-to-video")
def text_to_video(payload: TextToVideoIn) -> dict:
    prompts = [p.strip() for p in payload.prompts if p.strip()]
    if not prompts and payload.prompt.strip():
        prompts = [payload.prompt.strip()] * max(2, payload.scenes)
    if not prompts:
        raise HTTPException(status_code=400, detail="Provide a prompt or a list of scene prompts.")
    result = generate_scene_video(prompts, style_prefix=PHOTO_STYLES.get(payload.style, ""),
                                   width=payload.width, height=payload.height,
                                   duration_per_slide=payload.duration_per_slide)
    if not result:
        raise HTTPException(status_code=502, detail="Could not render a video (image generation or ffmpeg failed).")
    if payload.save_to_chat:
        label = prompts[0][:80] + ("…" if len(prompts) > 1 else "")
        save_message("assistant", f"🎥 *[Video: {label}]*", payload.session_id)
    return {
        "image_paths": result["image_paths"], "image_urls": [_media_url(p) for p in result["image_paths"]],
        "video_path": result["video_path"], "video_url": _media_url(result["video_path"]),
    }


@app.post("/api/voice/speak")
def voice_speak(payload: ChatEditIn) -> dict:
    try:
        from core.edge_voice import get_voice_for_character, speak_text
        path = speak_text(payload.content, voice=get_voice_for_character())
        return {"path": path, "url": _media_url(path)}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"TTS unavailable: {exc}") from exc


@app.get("/api/settings/value/{key}")
def read_setting(key: str, default: str = "") -> dict:
    return {"key": key, "value": get_setting(key, default)}


@app.post("/api/settings")
def write_setting(payload: SettingIn) -> dict:
    set_setting(payload.key, payload.value)
    return {"saved": True}


@app.post("/api/settings/bool")
def write_bool_setting(payload: BoolSettingIn) -> dict:
    from core.storage import set_bool_setting

    set_bool_setting(payload.key, payload.value)
    return {"saved": True}


@app.get("/api/settings/dashboard")
def settings_dashboard() -> dict:
    conn = get_conn()
    try:
        counts = {}
        for table in ["characters", "worlds", "messages", "knowledge_documents", "media_items", "quests", "relationships"]:
            counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        return {"counts": counts}
    finally:
        conn.close()


@app.post("/api/settings/import-test")
def settings_import_test() -> dict:
    from core.import_test import test_imports

    passed, failures = test_imports()
    return {"ok": len(failures) == 0, "passed": passed, "failures": failures}


@app.get("/api/settings/db-integrity")
def settings_db_integrity() -> dict:
    conn = get_conn()
    try:
        rows = conn.execute("PRAGMA integrity_check").fetchall()
        return {"result": [row[0] for row in rows]}
    finally:
        conn.close()


@app.post("/api/settings/backup")
def settings_create_backup() -> dict:
    from core.backup_restore import create_backup

    return {"path": create_backup()}


@app.get("/api/settings/backups")
def settings_backups() -> list[dict]:
    from core.backup_restore import list_backups

    return list_backups()


@app.get("/api/settings/model")
def settings_model() -> dict:
    from core.chat_engine import get_active_model

    return {"active_model": get_active_model()}


@app.post("/api/settings/model")
def settings_set_model(payload: SettingIn) -> dict:
    from core.chat_engine import set_active_model

    set_active_model(payload.value)
    return {"saved": True}


@app.get("/api/settings/system-preamble")
def settings_system_preamble() -> dict:
    from core.chat_engine import get_system_preamble

    return {"value": get_system_preamble()}


@app.post("/api/settings/system-preamble")
def settings_set_system_preamble(payload: SettingIn) -> dict:
    from core.chat_engine import set_system_preamble

    set_system_preamble(payload.value)
    return {"saved": True}


@app.get("/api/settings/soul/{character_name}")
def settings_soul(character_name: str) -> dict:
    from core.companion_soul import get_soul

    return get_soul(character_name)


@app.post("/api/settings/soul/{character_name}")
def settings_save_soul(character_name: str, payload: dict) -> dict:
    from core.companion_soul import save_soul

    save_soul(character_name, payload)
    return {"saved": True}


def _sync_world_from_text(world_id: int | None, text: str) -> None:
    if not world_id:
        return
    conn = get_conn()
    try:
        lowered = text.lower()
        for keyword, weather in {"storm": "storm", "rain": "rain", "snow": "snow", "sunny": "clear", "fog": "fog"}.items():
            if keyword in lowered:
                conn.execute("UPDATE worlds SET weather=? WHERE id=?", (weather, world_id))
                break
        for keyword, time_of_day in {"dawn": "dawn", "morning": "morning", "noon": "midday", "evening": "evening", "night": "night", "midnight": "midnight"}.items():
            if keyword in lowered:
                conn.execute("UPDATE worlds SET time_of_day=? WHERE id=?", (time_of_day, world_id))
                break
        conn.commit()
    finally:
        conn.close()


def _add_quest_item(character_id: int, quest: dict) -> None:
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO inventory (character_id,item_name,item_type,quantity,value,description,source,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (
                character_id,
                f"Quest: {quest.get('title', '')[:25]}",
                "quest_item",
                1,
                10,
                quest.get("description", "")[:60],
                "quest",
                now_iso(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


import math as _math, time as _time

_GAME_CLOCK = {}  # session_id -> {day, hour, minute, weather, season, temp}

WEATHERS = ['Clear','Cloudy','Overcast','Light Rain','Heavy Rain','Thunderstorm','Fog','Drizzle','Snow','Blizzard','Windy','Hail','Sandstorm','Aurora','Mist']
SEASONS = ['Spring','Summer','Autumn','Winter']

def _get_clock(session_id='default'):
    if session_id not in _GAME_CLOCK:
        _GAME_CLOCK[session_id] = {'day':1,'hour':8,'minute':0,'weather':'Clear','season':'Spring','temp':18}
    return _GAME_CLOCK[session_id]

@app.get("/api/world/clock")
def get_world_clock(session_id: str = "default") -> dict:
    clk = _get_clock(session_id)
    return dict(clk)

@app.post("/api/world/clock/advance")
def advance_world_clock(session_id: str = "default", minutes: int = 30) -> dict:
    import random as _random
    clk = _get_clock(session_id)
    total = clk['hour'] * 60 + clk['minute'] + minutes
    clk['minute'] = total % 60
    clk['hour'] = (total // 60) % 24
    if total // 60 >= 24:
        clk['day'] += 1
        clk['season'] = SEASONS[(clk['day'] // 90) % 4]
    if _random.random() < 0.15:
        clk['weather'] = _random.choice(WEATHERS)
        clk['temp'] = _random.randint(-5, 35)
    return dict(clk)

@app.post("/api/world/events/random")
def random_world_event(session_id: str = "default", world_id: int = 0) -> dict:
    import random as _random
    EVENTS = [
        "A wandering merchant arrives at the nearest settlement with rare goods.",
        "Strange lights are seen in the sky — locals whisper of portals opening.",
        "A faction scout is spotted observing the party from afar.",
        "An earthquake trembles through the region, shifting the landscape slightly.",
        "A local festival erupts in the nearest town — music and laughter fill the air.",
        "Dark clouds gather rapidly; a magical storm approaches.",
        "A courier delivers an urgent sealed message addressed to one of the party.",
        "Distant horns signal an army on the march somewhere beyond the horizon.",
        "A rare celestial event lights up the night sky — all magic is amplified.",
        "A travelling bard begins spinning tales about the party's deeds.",
        "Raiders have struck a nearby village — smoke rises on the horizon.",
        "A portal flickers to life unexpectedly, revealing a glimpse of another world.",
        "An ancient ruin is spotted nearby that wasn't there yesterday.",
        "A powerful beast has been sighted by terrified locals.",
        "A political assassination changes the balance of power in the region.",
    ]
    event = _random.choice(EVENTS)
    try:
        clk = _get_clock(session_id)
        enhanced = send_to_llm([
            {"role":"system","content":"You are a fantasy game narrator. Given a random event seed, expand it into one vivid sentence (max 40 words) that fits the current world state."},
            {"role":"user","content":f"Event seed: {event}\nDay {clk['day']}, {clk['hour']:02d}:00, {clk['weather']} weather, {clk['season']} season."}
        ], temperature=0.9, max_tokens=80)
        if enhanced and not enhanced.startswith('['):
            event = enhanced.strip()
    except Exception:
        pass
    return {"event": event, "day": _get_clock(session_id)['day']}


class ScenarioGenIn(BaseModel):
    world_name: str = ""
    story_preset: str = ""
    genre: str = ""
    session_id: str = "default"

@app.post("/api/scenario/generate")
def generate_scenario_text(payload: ScenarioGenIn) -> dict:
    try:
        prompt = f"World: {payload.world_name or 'Unknown'}\nGenre: {payload.genre or 'Fantasy'}\nStory preset: {payload.story_preset or 'Adventure'}"
        raw = send_to_llm([
            {"role":"system","content":"You are a tabletop RPG campaign designer. Given a world and story preset, write an opening campaign scenario in 2-3 vivid sentences (max 60 words) that hooks the player immediately. Write in second person ('You...'). No headers, just the scenario text."},
            {"role":"user","content":prompt}
        ], temperature=0.9, max_tokens=120)
        text = raw.strip() if raw and not raw.startswith('[') else ""
    except Exception:
        text = ""
    if not text:
        text = f"You stand at the threshold of {payload.world_name or 'a new world'}, where the fate of many hangs in the balance. The air crackles with {payload.genre or 'adventure'} as {payload.story_preset or 'your journey'} begins."
    return {"scenario": text}


class NpcCreateIn(BaseModel):
    name: str
    role: str = ""
    faction: str = ""
    location: str = ""
    disposition: str = "neutral"
    world_id: int = 0
    session_id: str = "default"

@app.get("/api/world/npcs")
def get_world_npcs_session(world_id: int = 0, session_id: str = "default") -> list:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM npcs WHERE world_id=? ORDER BY id DESC LIMIT 30",
            (world_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
    finally:
        conn.close()

@app.post("/api/world/npcs")
def create_world_npc_session(payload: NpcCreateIn) -> dict:
    import random as _random
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO npcs (name, profession, faction, mood, world_id, created_at) VALUES (?,?,?,?,?,?)",
            (payload.name, payload.role, payload.faction, payload.disposition, payload.world_id, now_iso())
        )
        conn.commit()
        return {"id": cur.lastrowid, "saved": True}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.post("/api/world/npcs/generate")
def generate_npc_session(world_id: int = 0, session_id: str = "default") -> dict:
    import random as _random
    DISPOSITIONS = ['friendly','neutral','hostile','suspicious','desperate','grateful']
    ROLES = ['innkeeper','guard','merchant','assassin','wizard','healer','thief','noble','farmer','warrior','spy','exile','rebel','scholar']
    disposition = _random.choice(DISPOSITIONS)
    role = _random.choice(ROLES)
    try:
        raw = send_to_llm([
            {"role":"system","content":"You are a fantasy NPC generator. Create a brief NPC description: name, one quirk, one secret (max 30 words total). Format: Name: X | Quirk: Y | Secret: Z"},
            {"role":"user","content":f"Generate a {disposition} {role}:"}
        ], temperature=0.95, max_tokens=80)
        parts = {p.split(':')[0].strip().lower(): p.split(':',1)[1].strip() for p in raw.split('|') if ':' in p}
        name = parts.get('name', f"{role.title()} #{_random.randint(100,999)}")
        quirk = parts.get('quirk', '')
        secret = parts.get('secret', '')
    except Exception:
        name = f"{role.title()} #{_random.randint(100,999)}"
        quirk = secret = ''
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO npcs (name, profession, faction, mood, world_id, created_at) VALUES (?,?,?,?,?,?)",
            (name, role, '', disposition, world_id, now_iso())
        )
        conn.commit()
        return {"id": cur.lastrowid, "name": name, "role": role, "disposition": disposition, "quirk": quirk, "secret": secret}
    except Exception as e:
        return {"name": name, "role": role, "disposition": disposition}
    finally:
        conn.close()


ASSETS_DIR = REACT_DIST / "assets"
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

if MEDIA_DIR.exists():
    app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")


@app.get("/styles.css", include_in_schema=False)
def worldweaver_styles():
    return FileResponse(REACT_DIST / "styles.css", media_type="text/css")


@app.get("/game.js", include_in_schema=False)
def worldweaver_script():
    return FileResponse(REACT_DIST / "game.js", media_type="application/javascript")


@app.get("/worldweaver-icon.png", include_in_schema=False)
def worldweaver_icon():
    return FileResponse(REACT_DIST / "worldweaver-icon.png", media_type="image/png")

@app.get("/{path:path}")
def frontend(path: str = ""):
    index = REACT_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    raise HTTPException(
        status_code=503,
        detail="React frontend has not been built. Run full_install.py or npm run build in frontend/react_app.",
    )
