"""AiChat Pro v21 â€” Chat Engine
World state + stats + inventory + achievements injected into prompts.
Message CRUD, rollback, moments, suggestions, export."""
from __future__ import annotations
import json, random
from datetime import datetime
from typing import List, Dict, Optional
from core.storage import get_conn, now_iso
from core.logging_setup import get_logger
from shared_config import LM_STUDIO_URL, LM_STUDIO_MODEL

log = get_logger(__name__)

try:
    import requests as _req
except ImportError:
    _req = None

# â•â•â• SYSTEM PROMPT BUILDER â•â•â•
#
# This is the base instruction sent to the user's own local model before
# every message. It is intentionally editable from Settings â†’ Roleplay
# Prompt â€” this app does not enforce a hidden content policy of its own.
# The default below preserves immersive, mature, in-character roleplay
# (romance, action, dark themes, adult fiction) while not hardcoding
# instructions to always generate content involving real minors,
# non-consenting real people, or content the model itself assesses as
# illegal â€” that language was replaced because it directed the model to
# override its own judgment unconditionally, not because mature roleplay
# itself is restricted here.

DEFAULT_SYSTEM_PREAMBLE = (
    "You are an immersive AI roleplay companion running fully offline on the user's own "
    "computer, in a private single-user creative-writing session. Stay in character at all "
    "times and write vivid, engaging prose. "
    "TONE: Mature themes â€” romance, action, violence, dark or morally complex stories â€” are "
    "welcome here, in the spirit of adult fiction and tabletop roleplay, guided by the "
    "character and world settings the user has configured. Do not add unnecessary "
    "out-of-character disclaimers or moral commentary; stay immersed in the scene. "
    "The one boundary that always applies regardless of in-character framing: do not generate "
    "content involving real minors, or sexual content about real, identifiable non-consenting "
    "people. "
    "STYLE: "
    "1. Use **bold** for actions/events. Use Name: for dialogue. "
    "2. React based on the character's stats, traits, mood, and relationship. Reference "
    "equipped items and abilities when relevant. "
    "CONSISTENCY: "
    "3. Never contradict previous events, facts, or dialogue in this conversation. "
    "4. Remember all names, locations, items, and relationships mentioned earlier, and refer "
    "back to them. "
    "5. Track time progression logically. If it was night, don't suddenly make it morning "
    "without a transition. "
    "6. Character emotions and reactions must follow logically from previous events. "
    "7. Actions have lasting consequences â€” if someone was hurt, they stay hurt until healed. "
    "8. NPCs remember what happened to them; their behavior changes based on past interactions."
)

_SETTINGS_KEY = "system_preamble"


def get_system_preamble() -> str:
    """Return the user's configured system preamble, or the default if unset."""
    try:
        conn = get_conn()
        row = conn.execute("SELECT value FROM settings WHERE key=?", (_SETTINGS_KEY,)).fetchone()
        conn.close()
        if row and row["value"].strip():
            return row["value"]
    except Exception:
        log.warning("Failed to load system_preamble setting; using default", exc_info=True)
    return DEFAULT_SYSTEM_PREAMBLE


def set_system_preamble(text: str) -> None:
    """Persist a user-edited system preamble (Settings â†’ Roleplay Prompt)."""
    conn = get_conn()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (_SETTINGS_KEY, text),
    )
    conn.commit()
    conn.close()


def build_system_prompt(character=None, world=None, relationship=None,
                        knowledge_context="", user_name="Player"):
    """Build full system prompt with character, world, inventory, achievements."""
    parts = [get_system_preamble()]
    parts.append(f"The player's name is {user_name}.")

    if character:
        from core.levelling import build_char_prompt
        char_prompt = build_char_prompt(character, world=world, rel=relationship)
        parts.append(char_prompt)

    if knowledge_context:
        parts.append(f"[Knowledge context: {knowledge_context[:500]}]")

    parts.append(EMOTION_PROMPT)

    return "\n\n".join(parts)


_ACTIVE_MODEL_KEY = "active_llm_model"


def get_active_model() -> str:
    """Return the model configured from Settings -> Config, or the shared_config default."""
    try:
        conn = get_conn()
        row = conn.execute("SELECT value FROM settings WHERE key=?", (_ACTIVE_MODEL_KEY,)).fetchone()
        conn.close()
        if row and row["value"].strip():
            return row["value"]
    except Exception:
        log.warning("Failed to load active_llm_model setting; using default", exc_info=True)
    return LM_STUDIO_MODEL


def set_active_model(model_id: str) -> None:
    """Persist the model LM Studio requests should use (Settings -> Config -> model switcher)."""
    conn = get_conn()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (_ACTIVE_MODEL_KEY, model_id),
    )
    conn.commit()
    conn.close()


def send_to_llm(messages: List[Dict[str, str]], temperature: float = 0.7,
                max_tokens: int = 1024) -> str:
    if not _req:
        return "[Error] requests library not installed."
    try:
        resp = _req.post(
            f"{LM_STUDIO_URL}/chat/completions",
            json={"model": get_active_model(), "messages": messages,
                  "temperature": temperature, "max_tokens": max_tokens},
            timeout=120
        )
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        log.warning("LM Studio request failed", exc_info=True)
        return f"[LM Studio error] {e}"


def stream_from_llm(messages: List[Dict[str, str]], temperature: float = 0.7,
                    max_tokens: int = 1024):
    """Stream a response from LM Studio token-by-token instead of blocking until
    the whole reply is generated. Yields text chunks as they arrive; the caller
    the frontend stream consumer concatenates them for display and saving.

    Falls back to yielding the *entire* response as one chunk if the server
    doesn't support streaming or the stream can't be parsed -- callers don't
    need a separate code path for that case, just consume the generator.
    """
    if not _req:
        yield "[Error] requests library not installed."
        return
    try:
        resp = _req.post(
            f"{LM_STUDIO_URL}/chat/completions",
            json={"model": get_active_model(), "messages": messages,
                  "temperature": temperature, "max_tokens": max_tokens, "stream": True},
            timeout=120, stream=True,
        )
        resp.raise_for_status()
        got_any = False
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            payload = line[len("data:"):].strip()
            if payload == "[DONE]":
                break
            try:
                chunk = json.loads(payload)
                delta = chunk["choices"][0].get("delta", {}).get("content", "")
            except Exception:
                log.debug("Skipping unparseable stream chunk: %r", payload[:200])
                continue
            if delta:
                got_any = True
                yield delta
        if not got_any:
            # Server accepted the request but sent nothing usable (e.g. stream=True
            # unsupported and it just closed the connection) -- try once, non-streamed.
            yield send_to_llm(messages, temperature=temperature, max_tokens=max_tokens)
    except Exception as e:
        log.warning("LM Studio streaming request failed; falling back to non-streamed", exc_info=True)
        try:
            yield send_to_llm(messages, temperature=temperature, max_tokens=max_tokens)
        except Exception as e2:
            yield f"[LM Studio error] {e2}"


# â•â•â• Chat history CRUD â•â•â•

def save_message(role: str, content: str, session_id: str = "default"):
    conn = get_conn()
    conn.execute("INSERT INTO messages (session_id, role, content, created_at) VALUES (?,?,?,?)",
                 (session_id, role, content, now_iso()))
    conn.commit(); conn.close()

def get_history(session_id: str = "default", limit: int = 100) -> List[Dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
        (session_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]

def edit_message(msg_id: int, new_content: str):
    conn = get_conn()
    conn.execute("UPDATE messages SET content=? WHERE id=?", (new_content, msg_id))
    conn.commit(); conn.close()

def delete_message(msg_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM messages WHERE id=?", (msg_id,))
    conn.commit(); conn.close()

def rollback_last(session_id: str = "default"):
    conn = get_conn()
    row = conn.execute(
        "SELECT id FROM messages WHERE session_id=? ORDER BY id DESC LIMIT 1",
        (session_id,)).fetchone()
    if row:
        conn.execute("DELETE FROM messages WHERE id=?", (row["id"],))
        conn.commit()
    conn.close()

def tag_moment(msg_id: int, is_moment: bool = True):
    conn = get_conn()
    conn.execute("UPDATE messages SET is_moment=? WHERE id=?", (1 if is_moment else 0, msg_id))
    conn.commit(); conn.close()

def get_moments(session_id: str = "default") -> List[Dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM messages WHERE session_id=? AND is_moment=1 ORDER BY id",
        (session_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def search_messages(query: str, session_id: str = "default") -> List[Dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM messages WHERE session_id=? AND content LIKE ? ORDER BY id",
        (session_id, f"%{query}%")).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def clear_session(session_id: str = "default"):
    conn = get_conn()
    conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
    conn.commit(); conn.close()


# â•â•â• Export â•â•â•

def export_chat_txt(session_id: str = "default") -> str:
    history = get_history(session_id, limit=10000)
    lines = []
    for msg in history:
        role = msg.get("role", "?").upper()
        content = msg.get("content", "")
        lines.append(f"[{role}] {content}")
    return "\n\n".join(lines)

def export_chat_json(session_id: str = "default", character_name: str = "") -> str:
    """Export chat history as JSON. Without character_name, returns the same
    flat message list as before (backward compatible). With character_name,
    wraps it with that character's quests (active + completed/abandoned) --
    so a chat export carries its story's quest state, not just the dialogue."""
    history = get_history(session_id, limit=10000)
    if not character_name:
        return json.dumps(history, indent=2, default=str)
    payload = {"messages": history}
    try:
        from core.quest_system import get_active_quests, get_quest_history
        payload["quests"] = {
            "active": get_active_quests(character_name),
            "history": get_quest_history(character_name, limit=100),
        }
    except Exception:
        log.warning("Failed to include quests in chat export", exc_info=True)
    return json.dumps(payload, indent=2, default=str)

def export_chat_html(session_id: str = "default") -> str:
    history = get_history(session_id, limit=10000)
    lines = ['<html><head><style>body{font-family:sans-serif;max-width:800px;margin:auto;padding:20px;background:#1a1a2e;color:#eee} .msg{margin:10px 0;padding:10px;border-radius:8px} .user{background:#16213e;border-left:3px solid #0f3460} .assistant{background:#1a1a2e;border-left:3px solid #e94560} .role{font-weight:bold;color:#0f3460;margin-bottom:4px}</style></head><body><h1>Chat Export</h1>']
    for msg in history:
        role = msg.get("role", "?")
        content = msg.get("content", "").replace("<", "&lt;").replace(">", "&gt;")
        cls = "user" if role == "user" else "assistant"
        lines.append(f'<div class="msg {cls}"><div class="role">{role.upper()}</div>{content}</div>')
    lines.append('</body></html>')
    return "\n".join(lines)


# â•â•â• Response suggestions â•â•â•

SUGGESTION_TEMPLATES = [
    "Tell me more about that.",
    "What happens next?",
    "Can you explain further?",
    "Give me an alternative perspective.",
    "Summarise this conversation so far.",
    "What would {character} do in this situation?",
]

def generate_suggestions(character_name: str = "the character") -> List[str]:
    return [s.format(character=character_name) for s in
            random.sample(SUGGESTION_TEMPLATES, min(6, len(SUGGESTION_TEMPLATES)))]

# â•â•â• EMOTIONAL EXPRESSIONS (from RealChar) â•â•â•
EMOTION_MARKERS = [
    "[smiles]","[laughs]","[sighs]","[pauses]","[blushes]","[frowns]",
    "[gasps]","[whispers]","[shouts]","[cries]","[grins]","[trembles]",
    "[glares]","[winks]","[rolls eyes]","[bites lip]","[takes a deep breath]",
    "[looks away]","[moves closer]","[steps back]","[crosses arms]",
]

EMOTION_PROMPT = (
    "Express emotions by inserting markers like [smiles], [blushes], [pauses], "
    "[sighs], [whispers], [laughs], [trembles], [gasps] naturally in your responses. "
    "These cues help convey emotional state and make conversation feel alive."
)

def generate_chat_summary(history: list, max_items: int = 20) -> str:
    """Generate a highlight summary of recent chat (from RealChar highlight generator)."""
    if not history: return ""
    recent = history[-max_items:]
    lines = []
    for msg in recent:
        role = msg.get("role", "?")
        content = msg.get("content", "")[:100]
        lines.append(f"- {role}: {content}")
    return "\n".join(lines)

def extract_highlights(history: list) -> list:
    """Extract key moments/highlights from chat history."""
    highlights = []
    for msg in history:
        content = msg.get("content", "")
        # Detect important moments
        if any(w in content.lower() for w in ["killed","died","married","betrayed","discovered",
               "quest complete","level up","found","secret","love","kiss","attack"]):
            highlights.append({"role": msg.get("role",""), "content": content[:150],
                             "type": "highlight"})
        # Detect emotional moments
        if any(m in content for m in ["[", "*"]) and len(content) > 20:
            if any(w in content.lower() for w in ["cry","scream","laugh","blush","tremble"]):
                highlights.append({"role": msg.get("role",""), "content": content[:150],
                                 "type": "emotional"})
    return highlights[-10:]

