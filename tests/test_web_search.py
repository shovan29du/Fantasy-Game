"""General web search via the Brave Search API (core/web_search.py).

All network calls are mocked. Verifies request construction, response
parsing, error surfacing, the missing-API-key case, and local-only mode --
never fabricates results locally.
"""
from unittest.mock import patch, MagicMock

from core.web_search import search_web, SETTINGS_KEY
from core.storage import set_bool_setting, set_setting


def _fake_response(results):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"web": {"results": results}}
    return resp


def test_search_web_without_api_key_returns_helpful_error(temp_db):
    results, error = search_web("dragons")
    assert results == []
    assert "API key" in error


def test_search_web_parses_real_response_shape(temp_db):
    set_setting(SETTINGS_KEY, "fake-key-123")
    items = [{"title": "Example", "url": "https://example.com", "description": "An example page."}]
    with patch("core.web_search._req") as mock_req:
        mock_req.get.return_value = _fake_response(items)
        results, error = search_web("dragons")
    assert error is None
    assert len(results) == 1
    assert results[0]["title"] == "Example"
    assert results[0]["url"] == "https://example.com"


def test_search_web_sends_api_key_header(temp_db):
    set_setting(SETTINGS_KEY, "fake-key-123")
    with patch("core.web_search._req") as mock_req:
        mock_req.get.return_value = _fake_response([])
        search_web("dragons", count=5)
    _, kwargs = mock_req.get.call_args
    assert kwargs["headers"]["X-Subscription-Token"] == "fake-key-123"
    assert kwargs["params"]["q"] == "dragons"
    assert kwargs["params"]["count"] == 5


def test_search_web_rejects_empty_query(temp_db):
    set_setting(SETTINGS_KEY, "fake-key-123")
    results, error = search_web("   ")
    assert results == []
    assert error is not None


def test_search_web_surfaces_401(temp_db):
    set_setting(SETTINGS_KEY, "bad-key")
    resp = MagicMock()
    resp.status_code = 401
    with patch("core.web_search._req") as mock_req:
        mock_req.get.return_value = resp
        results, error = search_web("dragons")
    assert results == []
    assert "401" in error


def test_search_web_surfaces_network_error(temp_db):
    set_setting(SETTINGS_KEY, "fake-key-123")
    with patch("core.web_search._req") as mock_req:
        mock_req.get.side_effect = ConnectionError("no internet")
        results, error = search_web("dragons")
    assert results == []
    assert error is not None


def test_search_web_respects_local_only_mode(temp_db):
    set_setting(SETTINGS_KEY, "fake-key-123")
    set_bool_setting("local_only_mode", True)
    with patch("core.web_search._req") as mock_req:
        results, error = search_web("dragons")
    mock_req.get.assert_not_called()
    assert results == []
    assert "Local-only mode" in error
