"""Journal: the player's notes plus a window onto what the storyteller remembers.

Everything here is scoped to one story (a chat session). Memory facts follow
the same visibility rule the storyteller uses when it recalls them, so what
the player sees in the Journal is exactly what can influence the next reply.
"""
from __future__ import annotations

import json
import re
from typing import Any

from core.memory_engine import STORY_FACTS_SQL
from core.storage import get_conn, now_iso

MEMORY_TYPES = ["episodic", "semantic", "procedural", "preference", "event", "general"]
IMPORTANCE_LEVELS = {"minor": 0.3, "normal": 0.5, "important": 0.8}
NOTE_KINDS = ["note", "recap", "clue", "todo"]
MAX_TEXT = 4000


def _clean(text: Any, limit: int = MAX_TEXT) -> str:
    return str(text or "").strip()[:limit]


def _tags(value: Any) -> str:
    """Tags stored as a comma-separated, lower-case, de-duplicated string."""
    items = value if isinstance(value, (list, tuple)) else str(value or "").split(",")
    seen: list[str] = []
    for item in items:
        tag = re.sub(r"\s+", " ", str(item).strip().lower())[:24]
        if tag and tag not in seen:
            seen.append(tag)
    return ",".join(seen[:8])


# ── Memory ───────────────────────────────────────────────────────────────

def _memory_row(row: dict) -> dict:
    importance = row.get("importance") or 0.5
    level = "important" if importance >= 0.7 else "normal" if importance >= 0.4 else "minor"
    return {
        "id": row["id"],
        "fact": row["fact"],
        "memory_type": row.get("memory_type") or "general",
        "importance": importance,
        "level": level,
        "pinned": bool(row.get("pinned")),
        "source": row.get("source") or "",
        "origin": "auto" if row.get("source") == "auto" else "you",
        "character_name": row.get("character_name") or "",
        "scope": "story" if row.get("session_id") else "shared",
        "created_at": row.get("created_at") or "",
    }


def list_memory(session_id: str, query: str = "", memory_type: str = "", view: str = "story") -> list[dict]:
    """Facts the story can recall (view='story'), or facts that no story owns
    (view='legacy': auto-captured before facts were tied to a story)."""
    conn = get_conn()
    try:
        if view == "legacy":
            rows = conn.execute(
                "SELECT * FROM memory_facts WHERE COALESCE(session_id,'')='' AND source='auto' ORDER BY id DESC LIMIT 300"
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT * FROM memory_facts WHERE {STORY_FACTS_SQL} "
                "ORDER BY COALESCE(pinned,0) DESC, importance DESC, id DESC LIMIT 500", (session_id,)
            ).fetchall()
    finally:
        conn.close()
    items = [_memory_row(dict(r)) for r in rows]
    if memory_type:
        items = [m for m in items if m["memory_type"] == memory_type]
    words = query.lower().split()
    if words:
        items = [m for m in items if all(w in (m["fact"] + " " + m["character_name"] + " " + m["memory_type"]).lower() for w in words)]
    return items


def update_memory(fact_id: int, fields: dict) -> dict | None:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM memory_facts WHERE id=?", (fact_id,)).fetchone()
        if not row:
            return None
        row = dict(row)
        fact = _clean(fields["fact"], 600) if "fact" in fields else row["fact"]
        if not fact:
            raise ValueError("A memory cannot be empty.")
        memory_type = fields.get("memory_type", row.get("memory_type") or "general")
        if memory_type not in MEMORY_TYPES:
            raise ValueError(f"Unknown memory type: {memory_type}")
        pinned = int(bool(fields["pinned"])) if "pinned" in fields else int(bool(row.get("pinned")))
        importance = row.get("importance") or 0.5
        if "level" in fields:
            if fields["level"] not in IMPORTANCE_LEVELS:
                raise ValueError(f"Unknown importance: {fields['level']}")
            importance = IMPORTANCE_LEVELS[fields["level"]]
        if pinned:
            importance = 1.0
        elif "pinned" in fields and "level" not in fields:
            importance = IMPORTANCE_LEVELS["important"]  # unpinning keeps it prominent
        session_id = row.get("session_id") or ""
        if "session_id" in fields:
            session_id = fields["session_id"] or ""
        conn.execute(
            "UPDATE memory_facts SET fact=?, memory_type=?, importance=?, pinned=?, session_id=? WHERE id=?",
            (fact, memory_type, importance, pinned, session_id, fact_id),
        )
        conn.commit()
        row.update(fact=fact, memory_type=memory_type, importance=importance, pinned=pinned, session_id=session_id)
        return _memory_row(row)
    finally:
        conn.close()


def delete_memory(fact_id: int) -> bool:
    conn = get_conn()
    try:
        cur = conn.execute("DELETE FROM memory_facts WHERE id=?", (fact_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def memory_counts(session_id: str) -> dict:
    conn = get_conn()
    try:
        story = conn.execute(f"SELECT COUNT(*) FROM memory_facts WHERE {STORY_FACTS_SQL}", (session_id,)).fetchone()[0]
        pinned = conn.execute(
            f"SELECT COUNT(*) FROM memory_facts WHERE {STORY_FACTS_SQL} AND COALESCE(pinned,0)=1", (session_id,)
        ).fetchone()[0]
        legacy = conn.execute(
            "SELECT COUNT(*) FROM memory_facts WHERE COALESCE(session_id,'')='' AND source='auto'"
        ).fetchone()[0]
    finally:
        conn.close()
    return {"story": story, "pinned": pinned, "legacy": legacy}


# ── Notes ────────────────────────────────────────────────────────────────

def _note_row(row: dict) -> dict:
    return {
        "id": row["id"], "title": row["title"], "body": row["body"], "kind": row.get("kind") or "note",
        "tags": [t for t in (row.get("tags") or "").split(",") if t], "pinned": bool(row["pinned"]),
        "created_at": row["created_at"], "updated_at": row["updated_at"],
    }


def list_notes(session_id: str, query: str = "", tag: str = "", kind: str = "") -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM journal_notes WHERE session_id=? ORDER BY pinned DESC, updated_at DESC, id DESC", (session_id,)
        ).fetchall()
    finally:
        conn.close()
    notes = [_note_row(dict(r)) for r in rows]
    if tag:
        notes = [n for n in notes if tag.lower() in n["tags"]]
    if kind:
        notes = [n for n in notes if n["kind"] == kind]
    words = query.lower().split()
    if words:
        notes = [n for n in notes if all(w in (n["title"] + " " + n["body"] + " " + " ".join(n["tags"])).lower() for w in words)]
    return notes


def create_note(session_id: str, title: str = "", body: str = "", tags: Any = "", kind: str = "note",
                pinned: bool = False) -> dict:
    title, body = _clean(title, 120), _clean(body)
    if not title and not body:
        raise ValueError("A note needs a title or some text.")
    if kind not in NOTE_KINDS:
        raise ValueError(f"Unknown note kind: {kind}")
    now = now_iso()
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO journal_notes (session_id, title, body, tags, pinned, kind, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (session_id, title, body, _tags(tags), int(pinned), kind, now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM journal_notes WHERE id=?", (cur.lastrowid,)).fetchone()
        return _note_row(dict(row))
    finally:
        conn.close()


def update_note(note_id: int, fields: dict) -> dict | None:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM journal_notes WHERE id=?", (note_id,)).fetchone()
        if not row:
            return None
        row = dict(row)
        title = _clean(fields["title"], 120) if "title" in fields else row["title"]
        body = _clean(fields["body"]) if "body" in fields else row["body"]
        if not title and not body:
            raise ValueError("A note needs a title or some text.")
        kind = fields.get("kind", row["kind"])
        if kind not in NOTE_KINDS:
            raise ValueError(f"Unknown note kind: {kind}")
        tags = _tags(fields["tags"]) if "tags" in fields else row["tags"]
        pinned = int(bool(fields["pinned"])) if "pinned" in fields else row["pinned"]
        conn.execute(
            "UPDATE journal_notes SET title=?, body=?, tags=?, pinned=?, kind=?, updated_at=? WHERE id=?",
            (title, body, tags, pinned, kind, now_iso(), note_id),
        )
        conn.commit()
        return _note_row(dict(conn.execute("SELECT * FROM journal_notes WHERE id=?", (note_id,)).fetchone()))
    finally:
        conn.close()


def delete_note(note_id: int) -> bool:
    conn = get_conn()
    try:
        cur = conn.execute("DELETE FROM journal_notes WHERE id=?", (note_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ── People ───────────────────────────────────────────────────────────────

def people(session_id: str, character_id: int | None = None) -> list[dict]:
    """Everyone the player has dealt with in this story: how they feel (trust,
    bond, mood), recent events, and what the player has recorded about them."""
    suffix = f" [{session_id}]"
    conn = get_conn()
    try:
        rel_rows = conn.execute("SELECT * FROM relationships WHERE character_name LIKE ?", (f"%{suffix}",)).fetchall()
        facts = {}
        if character_id:
            for r in conn.execute(
                "SELECT npc_name, fact, created_at FROM npc_memory WHERE character_id=? AND session_id IN (?, '') "
                "ORDER BY id DESC", (character_id, session_id)
            ).fetchall():
                facts.setdefault(r["npc_name"], []).append(r["fact"])
        out: dict[str, dict] = {}
        for r in rel_rows:
            r = dict(r)
            name = r["character_name"][: -len(suffix)]
            events = [dict(e) for e in conn.execute(
                "SELECT sentiment, trust_delta, note, created_at FROM relationship_events WHERE character_name=? "
                "ORDER BY id DESC LIMIT 4", (r["character_name"],)
            ).fetchall()]
            out[name] = {
                "name": name, "trust": r["trust_score"], "bond": r["bond_level"], "mood": r["mood"],
                "interactions": r["interaction_count"], "events": events, "facts": facts.pop(name, []),
            }
        for name, notes in facts.items():
            out[name] = {"name": name, "trust": None, "bond": "", "mood": "", "interactions": 0, "events": [], "facts": notes}
    finally:
        conn.close()
    return sorted(out.values(), key=lambda p: (p["trust"] is None, -(p["interactions"] or 0), p["name"]))


# ── Recap ────────────────────────────────────────────────────────────────

def recap_prompt(session_id: str, limit: int = 40) -> list[dict] | None:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?", (session_id, limit)
        ).fetchall()
    finally:
        conn.close()
    if len(rows) < 2:
        return None
    transcript = "\n".join(f"{r['role']}: {str(r['content'])[:500]}" for r in reversed(rows))
    return [
        {"role": "system", "content": (
            "You keep a campaign journal. Summarise the story so far from the transcript below in 4 to 7 short "
            "bullet points covering: where the player is, who they have met, what they want, any open threads or "
            "promises, and any danger ahead. Plain text, one bullet per line starting with '- '. No preamble.")},
        {"role": "user", "content": transcript},
    ]


def counts(session_id: str, quests_active: int = 0) -> dict:
    conn = get_conn()
    try:
        notes = conn.execute("SELECT COUNT(*) FROM journal_notes WHERE session_id=?", (session_id,)).fetchone()[0]
        moments = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE session_id=? AND is_moment=1", (session_id,)
        ).fetchone()[0]
    finally:
        conn.close()
    return {"notes": notes, "moments": moments, "memory": memory_counts(session_id), "quests": quests_active}
