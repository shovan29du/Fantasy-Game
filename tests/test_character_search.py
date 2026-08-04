"""Real web character search against chub.ai (core/character_search.py).

All network calls are mocked -- these verify request construction, response
parsing, the PNG-embedded-card extraction, error surfacing, and local-only
mode enforcement. None of this fabricates character data locally; a failure
must show up as an error, never as fake results.
"""
import base64
import io
import json
from unittest.mock import patch, MagicMock

from core.character_search import search_characters, fetch_character_card, _extract_card_json
from core.storage import set_bool_setting


def _fake_search_response(nodes):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"nodes": nodes}
    return resp


def test_search_characters_parses_real_response_shape(temp_db):
    nodes = [{
        "name": "Aria the Bold", "tagline": "A knight seeking redemption.",
        "topics": ["fantasy", "knight"], "fullPath": "someauthor/aria-the-bold",
        "n_favorites": 42,
    }]
    with patch("core.character_search._req") as mock_req:
        mock_req.get.return_value = _fake_search_response(nodes)
        results, error = search_characters(query="knight")
    assert error is None
    assert len(results) == 1
    r = results[0]
    assert r["name"] == "Aria the Bold"
    assert r["author"] == "someauthor"
    assert r["full_path"] == "someauthor/aria-the-bold"
    assert "fantasy" in r["tags"]
    assert r["page_url"] == "https://chub.ai/characters/someauthor/aria-the-bold"


def test_search_characters_sends_expected_params(temp_db):
    with patch("core.character_search._req") as mock_req:
        mock_req.get.return_value = _fake_search_response([])
        search_characters(query="dragon", tags=["fantasy", "romance"], nsfw=False, count=10)
    args, kwargs = mock_req.get.call_args
    assert kwargs["params"]["search"] == "dragon"
    assert kwargs["params"]["tags"] == "fantasy,romance"
    assert kwargs["params"]["nsfw"] == "false"
    assert kwargs["params"]["first"] == 10


def test_search_characters_never_fabricates_on_network_error(temp_db):
    with patch("core.character_search._req") as mock_req:
        mock_req.get.side_effect = ConnectionError("no internet")
        results, error = search_characters(query="anything")
    assert results == []
    assert error is not None
    assert "chub.ai" in error


def test_search_characters_surfaces_403(temp_db):
    resp = MagicMock()
    resp.status_code = 403
    with patch("core.character_search._req") as mock_req:
        mock_req.get.return_value = resp
        results, error = search_characters()
    assert results == []
    assert "403" in error


def test_search_characters_retries_without_sort_on_422(temp_db):
    """A 422 most likely means our guessed `sort` enum was wrong -- retry once
    without it instead of failing the whole search."""
    resp422 = MagicMock()
    resp422.status_code = 422
    resp422.json.return_value = {"message": "invalid sort value"}
    resp200 = _fake_search_response([])
    with patch("core.character_search._req") as mock_req:
        mock_req.get.side_effect = [resp422, resp200]
        results, error = search_characters(query="x", sort="star_count")
    assert error is None
    assert results == []
    assert mock_req.get.call_count == 2
    _, kwargs = mock_req.get.call_args
    assert "sort" not in kwargs["params"]


def test_search_characters_surfaces_422_detail_if_retry_also_fails(temp_db):
    resp422a = MagicMock()
    resp422a.status_code = 422
    resp422a.json.return_value = {"message": "invalid sort value"}
    resp422b = MagicMock()
    resp422b.status_code = 422
    resp422b.json.return_value = {"message": "search param also invalid"}
    with patch("core.character_search._req") as mock_req:
        mock_req.get.side_effect = [resp422a, resp422b]
        results, error = search_characters(query="x", sort="star_count")
    assert results == []
    assert "422" in error
    assert "search param also invalid" in error


def test_search_characters_surfaces_response_body_on_error(temp_db):
    resp = MagicMock()
    resp.status_code = 500
    resp.json.return_value = {"message": "internal server error detail"}
    with patch("core.character_search._req") as mock_req:
        mock_req.get.return_value = resp
        results, error = search_characters()
    assert results == []
    assert "500" in error
    assert "internal server error detail" in error


def test_search_characters_respects_local_only_mode(temp_db):
    set_bool_setting("local_only_mode", True)
    with patch("core.character_search._req") as mock_req:
        results, error = search_characters(query="anything")
    mock_req.get.assert_not_called()
    assert results == []
    assert "Local-only mode" in error


def test_extract_card_json_reads_embedded_png_text_chunk():
    from PIL import Image, PngImagePlugin
    card = {"data": {"name": "Aria", "description": "A brave knight.",
                      "personality": "Bold", "scenario": "A quest begins.",
                      "first_mes": "Hello!", "tags": ["fantasy"]}}
    raw = base64.b64encode(json.dumps(card).encode()).decode()
    img = Image.new("RGB", (10, 10))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("chara", raw)
    buf = io.BytesIO()
    img.save(buf, "PNG", pnginfo=meta)

    result = _extract_card_json(buf.getvalue())
    assert result["name"] == "Aria"
    assert result["personality"] == "Bold"
    assert result["scenario"] == "A quest begins."


def test_extract_card_json_handles_v1_flat_format():
    from PIL import Image, PngImagePlugin
    card = {"name": "Bram", "description": "A grim warrior.", "personality": "Stoic"}
    raw = base64.b64encode(json.dumps(card).encode()).decode()
    img = Image.new("RGB", (10, 10))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("chara", raw)
    buf = io.BytesIO()
    img.save(buf, "PNG", pnginfo=meta)

    result = _extract_card_json(buf.getvalue())
    assert result["name"] == "Bram"


def test_extract_card_json_returns_none_for_image_without_embedded_data():
    from PIL import Image
    img = Image.new("RGB", (10, 10))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    assert _extract_card_json(buf.getvalue()) is None


def test_fetch_character_card_returns_none_on_http_error(temp_db):
    resp = MagicMock()
    resp.status_code = 500
    with patch("core.character_search._req") as mock_req:
        mock_req.post.return_value = resp
        assert fetch_character_card("someauthor/x") is None


def test_fetch_character_card_respects_local_only_mode(temp_db):
    set_bool_setting("local_only_mode", True)
    with patch("core.character_search._req") as mock_req:
        result = fetch_character_card("someauthor/x")
    mock_req.post.assert_not_called()
    assert result is None
