"""AiChat Pro — Web Character Search
Searches chub.ai's public character-card catalog (the same public API used by
the well-known SillyTavern-Chub-Search extension) for real, community-authored
companion characters. Nothing here is fabricated locally -- results are only
ever what the API actually returns, and every network failure is surfaced to
the caller rather than papered over with fake data.

Character cards on chub.ai are PNG images with the full character JSON
(personality, scenario, opening message, etc.) embedded in a PNG text chunk
per the "character card" convention shared by SillyTavern/TavernAI/KoboldAI.
"""
from __future__ import annotations
import base64
import io
import json
from typing import Dict, List, Optional, Tuple

from core.logging_setup import get_logger

log = get_logger(__name__)

try:
    import requests as _req
except ImportError:
    _req = None

try:
    from PIL import Image
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

SEARCH_URL = "https://api.chub.ai/api/characters/search"
DOWNLOAD_URL = "https://api.chub.ai/api/characters/download"
CARD_PAGE_URL = "https://chub.ai/characters/{full_path}"

# A plain "python-requests" UA is more likely to be blocked by bot protection
# than a browser-like one; this doesn't guarantee success, but it's the same
# courtesy the reference SillyTavern extension's browser fetch() gets for free.
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json",
}


def _error_detail(resp) -> str:
    """Best-effort snippet of a non-2xx response body, so failures are
    self-diagnosing instead of just a bare status code."""
    try:
        body = resp.json()
        if isinstance(body, dict):
            detail = body.get("message") or body.get("error") or body.get("detail") or body
        else:
            detail = body
        text = json.dumps(detail) if not isinstance(detail, str) else detail
    except Exception:
        text = (resp.text or "").strip()
    return text[:300]


def _local_only_blocked() -> Optional[str]:
    try:
        from core.storage import get_bool_setting
        if get_bool_setting("local_only_mode", False):
            return ("Local-only mode is on (Settings -> Config), so web character search "
                    "is disabled. Turn it off to search chub.ai.")
    except Exception:
        log.debug("suppressed error", exc_info=True)
    return None


def search_characters(query: str = "", tags: Optional[List[str]] = None,
                      nsfw: bool = True, sort: str = "star_count",
                      page: int = 1, count: int = 20,
                      timeout: int = 15) -> Tuple[List[Dict], Optional[str]]:
    """Search chub.ai's public character catalog. Returns (results, error) --
    results is [] and error is set on any failure; never fabricates data."""
    blocked = _local_only_blocked()
    if blocked:
        return [], blocked
    if not _req:
        return [], "The 'requests' library isn't installed — run: pip install requests"

    params = {
        "search": query or "",
        "first": max(1, min(count, 50)),
        "page": max(1, page),
        "sort": sort,
        "asc": "false",
        "venus": "true",
        "nsfw": "true" if nsfw else "false",
    }
    if tags:
        params["tags"] = ",".join(t.strip() for t in tags if t.strip())

    try:
        resp = _req.get(SEARCH_URL, params=params, headers=_HEADERS, timeout=timeout)
    except Exception as e:
        log.warning("chub.ai search request failed", exc_info=True)
        return [], f"Couldn't reach chub.ai: {e}"

    if resp.status_code == 422 and "sort" in params:
        # 422 = the server rejected a parameter value, most likely our guessed
        # `sort` enum (chub.ai's accepted values aren't publicly documented).
        # Retry once without it so a bad guess doesn't take the whole search down.
        log.warning("chub.ai rejected sort=%r (HTTP 422); retrying without it: %s",
                    sort, _error_detail(resp))
        retry_params = {k: v for k, v in params.items() if k != "sort"}
        try:
            resp = _req.get(SEARCH_URL, params=retry_params, headers=_HEADERS, timeout=timeout)
        except Exception as e:
            return [], f"Couldn't reach chub.ai: {e}"

    if resp.status_code == 403:
        return [], ("chub.ai returned 403 Forbidden — it may be rate-limiting or blocking "
                    "automated requests right now. Try again in a bit.")
    if resp.status_code != 200:
        return [], f"chub.ai returned HTTP {resp.status_code}: {_error_detail(resp)}"

    try:
        data = resp.json()
        nodes = data.get("nodes") or data.get("data", {}).get("nodes") or []
    except Exception as e:
        log.warning("Failed to parse chub.ai search response", exc_info=True)
        return [], f"Couldn't parse chub.ai's response: {e}"

    results = []
    for node in nodes:
        full_path = node.get("fullPath", "")
        results.append({
            "name": node.get("name", "Unknown"),
            "tagline": node.get("tagline", ""),
            "tags": node.get("topics", []) or [],
            "full_path": full_path,
            "author": full_path.split("/")[0] if "/" in full_path else "",
            "n_favorites": node.get("n_favorites") or node.get("starCount"),
            "page_url": CARD_PAGE_URL.format(full_path=full_path) if full_path else "",
            "source": "chub.ai",
        })
    return results, None


def fetch_character_card(full_path: str, timeout: int = 20) -> Optional[Dict]:
    """Download a character's full card and extract the embedded JSON (name,
    personality, description, scenario, first_mes, tags). Returns None if the
    download or extraction fails for any reason -- callers should fall back
    to the lighter search-result fields rather than treat this as fatal."""
    blocked = _local_only_blocked()
    if blocked or not _req:
        return None
    try:
        resp = _req.post(
            DOWNLOAD_URL, json={"fullPath": full_path, "format": "tavern", "version": "main"},
            headers=_HEADERS, timeout=timeout,
        )
        if resp.status_code != 200:
            return None
        return _extract_card_json(resp.content)
    except Exception:
        log.warning("fetch_character_card failed for %s", full_path, exc_info=True)
        return None


def _extract_card_json(png_bytes: bytes) -> Optional[Dict]:
    """Character cards embed their JSON in a PNG text chunk (keyword 'chara' or
    'ccv3'), base64-encoded, per the community character-card convention."""
    if not _PIL_OK:
        log.info("Pillow not installed; can't read embedded character card JSON")
        return None
    try:
        img = Image.open(io.BytesIO(png_bytes))
        text_chunks = getattr(img, "text", None) or img.info
        raw = text_chunks.get("chara") or text_chunks.get("ccv3")
        if not raw:
            return None
        decoded = base64.b64decode(raw)
        parsed = json.loads(decoded)
        # Character Card v2/v3 nests the real fields under "data"; v1 is flat.
        fields = parsed.get("data", parsed)
        return {
            "name": fields.get("name", ""),
            "description": fields.get("description", ""),
            "personality": fields.get("personality", ""),
            "scenario": fields.get("scenario", ""),
            "first_mes": fields.get("first_mes", ""),
            "mes_example": fields.get("mes_example", ""),
            "tags": fields.get("tags", []),
        }
    except Exception:
        log.warning("Failed to extract character card JSON from PNG", exc_info=True)
        return None
