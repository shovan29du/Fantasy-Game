"""AiChat Pro — Lorebook (from Backyard.ai)
Keyword-triggered world knowledge entries injected into chat context."""

from core.logging_setup import get_logger

log = get_logger(__name__)
import json, re
from typing import List, Dict
from core.storage import get_conn, now_iso

def create_entry(title: str, content: str, keywords: List[str], world_id: int = 0,
                 priority: int = 0, always_active: bool = False, case_sensitive: bool = False) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO lorebook (title, content, keywords_json, world_id, priority, "
                "always_active, case_sensitive, enabled, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (title, content, json.dumps(keywords), world_id, priority,
                 1 if always_active else 0, 1 if case_sensitive else 0, 1, now_iso()))
    eid = cur.lastrowid
    conn.commit(); conn.close()
    return eid

def get_triggered_entries(text: str, world_id: int = 0) -> List[Dict]:
    """Find lorebook entries whose keywords appear in the text."""
    conn = get_conn()
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM lorebook WHERE enabled=1 ORDER BY priority DESC").fetchall()]
    conn.close()
    triggered = []
    for r in rows:
        if r.get("always_active"):
            triggered.append(r); continue
        try: keywords = json.loads(r.get("keywords_json", "[]"))
        except Exception:
            log.debug("suppressed error", exc_info=True)
            keywords = []
        case = r.get("case_sensitive", 0)
        check = text if case else text.lower()
        for kw in keywords:
            match_kw = kw if case else kw.lower()
            if match_kw in check:
                triggered.append(r); break
    return triggered

def build_lorebook_context(text: str, world_id: int = 0, max_entries: int = 5) -> str:
    """Build lorebook context for chat prompt injection."""
    entries = get_triggered_entries(text, world_id)[:max_entries]
    if not entries: return ""
    parts = ["[World Knowledge:]"]
    for e in entries:
        parts.append(f"- {e['title']}: {e['content'][:200]}")
    return "\n".join(parts)

def list_entries(world_id: int = 0) -> List[Dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM lorebook ORDER BY priority DESC, title").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_entry(entry_id: int):
    conn = get_conn(); conn.execute("DELETE FROM lorebook WHERE id=?", (entry_id,))
    conn.commit(); conn.close()

def toggle_entry(entry_id: int, enabled: bool):
    conn = get_conn(); conn.execute("UPDATE lorebook SET enabled=? WHERE id=?", (1 if enabled else 0, entry_id))
    conn.commit(); conn.close()
