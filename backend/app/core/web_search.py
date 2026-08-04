"""AiChat Pro — General Web Search (Brave Search API)

chub.ai (core/character_search.py) only covers one character-card catalog.
For real "search the whole web" results this uses the Brave Search API --
a public, documented, stable REST API (unlike chub.ai's unofficial one) --
so results are genuine web pages, never fabricated locally.

Requires a free API key from https://brave.com/search/api/, entered in
Settings -> Config. Without a key, search_web() returns a clear error
instead of silently doing nothing or making something up.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple

from core.logging_setup import get_logger

log = get_logger(__name__)

try:
    import requests as _req
except ImportError:
    _req = None

SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
SETTINGS_KEY = "brave_search_api_key"


def _local_only_blocked() -> Optional[str]:
    try:
        from core.storage import get_bool_setting
        if get_bool_setting("local_only_mode", False):
            return ("Local-only mode is on (Settings -> Config), so web search "
                    "is disabled. Turn it off to search the web.")
    except Exception:
        log.debug("suppressed error", exc_info=True)
    return None


def _error_detail(resp) -> str:
    try:
        body = resp.json()
        if isinstance(body, dict):
            detail = body.get("message") or body.get("error") or body
        else:
            detail = body
        text = detail if isinstance(detail, str) else str(detail)
    except Exception:
        text = (resp.text or "").strip()
    return text[:300]


def search_web(query: str, count: int = 10, timeout: int = 15) -> Tuple[List[Dict], Optional[str]]:
    """Search the general web via the Brave Search API. Returns (results, error) --
    results is [] and error is set on any failure; never fabricates data."""
    blocked = _local_only_blocked()
    if blocked:
        return [], blocked
    if not _req:
        return [], "The 'requests' library isn't installed — run: pip install requests"

    from core.storage import get_setting
    api_key = get_setting(SETTINGS_KEY, "")
    if not api_key:
        return [], ("No Brave Search API key configured. Get a free one at "
                    "https://brave.com/search/api/ and add it in Settings -> Config "
                    "to enable whole-web search.")
    if not query.strip():
        return [], "Enter a search query."

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    params = {"q": query, "count": max(1, min(count, 20))}

    try:
        resp = _req.get(SEARCH_URL, params=params, headers=headers, timeout=timeout)
    except Exception as e:
        log.warning("Brave web search request failed", exc_info=True)
        return [], f"Couldn't reach the web search API: {e}"

    if resp.status_code == 401:
        return [], "Brave Search API rejected the key (401) — check it in Settings -> Config."
    if resp.status_code == 429:
        return [], "Brave Search API rate limit hit (429) — try again shortly."
    if resp.status_code != 200:
        return [], f"Web search returned HTTP {resp.status_code}: {_error_detail(resp)}"

    try:
        data = resp.json()
        items = (data.get("web") or {}).get("results") or []
    except Exception as e:
        log.warning("Failed to parse Brave search response", exc_info=True)
        return [], f"Couldn't parse the web search response: {e}"

    results = [{
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "description": item.get("description", ""),
        "source": "web",
    } for item in items]
    return results, None
