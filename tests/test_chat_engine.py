"""System prompt configurability and safety (core/chat_engine.py)."""
from unittest.mock import patch, MagicMock

import core.chat_engine as chat_engine
from core.chat_engine import (
    DEFAULT_SYSTEM_PREAMBLE, build_system_prompt, get_system_preamble, set_system_preamble,
    get_active_model, set_active_model, send_to_llm, stream_from_llm,
)


def _fake_stream_response(lines):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.iter_lines.return_value = lines
    return resp


def test_default_preamble_has_no_unsafe_absolute_language():
    lowered = DEFAULT_SYSTEM_PREAMBLE.lower()
    for banned in ("no restrictions", "no refusals", "no limits", "everything",
                   "incest roleplay", "non-con roleplay", "never refuse"):
        assert banned not in lowered


def test_get_system_preamble_defaults(temp_db):
    assert get_system_preamble() == DEFAULT_SYSTEM_PREAMBLE


def test_set_and_get_system_preamble_roundtrip(temp_db):
    set_system_preamble("Custom test prompt for my story.")
    assert get_system_preamble() == "Custom test prompt for my story."

    # Overwriting must update, not duplicate, the settings row.
    set_system_preamble("Second version.")
    assert get_system_preamble() == "Second version."


def test_build_system_prompt_includes_configured_preamble(temp_db):
    set_system_preamble("MY-UNIQUE-MARKER")
    prompt = build_system_prompt(user_name="Tester")
    assert "MY-UNIQUE-MARKER" in prompt
    assert "Tester" in prompt


def test_active_model_defaults_to_shared_config(temp_db):
    from shared_config import LM_STUDIO_MODEL
    assert get_active_model() == LM_STUDIO_MODEL


def test_set_and_get_active_model_roundtrip(temp_db):
    set_active_model("my-custom-model-7b")
    assert get_active_model() == "my-custom-model-7b"
    set_active_model("second-model")
    assert get_active_model() == "second-model"


def test_send_to_llm_uses_active_model(temp_db):
    """send_to_llm must request the settings-configured model, not the shared_config default."""
    set_active_model("switched-model")
    fake_response = MagicMock()
    fake_response.json.return_value = {"choices": [{"message": {"content": "hello there"}}]}
    with patch.object(chat_engine, "_req") as mock_req:
        mock_req.post.return_value = fake_response
        result = send_to_llm([{"role": "user", "content": "hi"}])
    assert result == "hello there"
    _, kwargs = mock_req.post.call_args
    assert kwargs["json"]["model"] == "switched-model"


def test_send_to_llm_handles_connection_errors_without_raising(temp_db):
    with patch.object(chat_engine, "_req") as mock_req:
        mock_req.post.side_effect = ConnectionError("LM Studio is not running")
        result = send_to_llm([{"role": "user", "content": "hi"}])
    assert "LM Studio is not running" in result
    assert result.startswith("[LM Studio error]")


def test_send_to_llm_without_requests_library():
    with patch.object(chat_engine, "_req", None):
        result = send_to_llm([{"role": "user", "content": "hi"}])
    assert "not installed" in result


def test_export_chat_json_backward_compatible_without_character(temp_db):
    from core.chat_engine import save_message, export_chat_json
    import json as _json
    save_message("user", "hello", "s1")
    result = _json.loads(export_chat_json("s1"))
    assert isinstance(result, list)
    assert result[0]["content"] == "hello"


def test_export_chat_json_includes_quests_with_character(temp_db):
    from core.chat_engine import save_message, export_chat_json
    from core.quest_system import generate_quest
    import json as _json
    save_message("user", "hello", "s1")
    generate_quest("Aria", qtype="story")
    result = _json.loads(export_chat_json("s1", character_name="Aria"))
    assert "messages" in result and "quests" in result
    assert len(result["quests"]["active"]) == 1


def test_stream_from_llm_yields_deltas_in_order(temp_db):
    lines = [
        'data: {"choices":[{"delta":{"content":"Hello"}}]}',
        'data: {"choices":[{"delta":{"content":", world"}}]}',
        'data: {"choices":[{"delta":{"content":"!"}}]}',
        'data: [DONE]',
    ]
    with patch.object(chat_engine, "_req") as mock_req:
        mock_req.post.return_value = _fake_stream_response(lines)
        chunks = list(stream_from_llm([{"role": "user", "content": "hi"}]))
    assert chunks == ["Hello", ", world", "!"]
    assert "".join(chunks) == "Hello, world!"


def test_stream_from_llm_requests_streaming_mode(temp_db):
    # Include a real delta so there's no content-less fallback call to confuse
    # which invocation of post() we're inspecting.
    lines = ['data: {"choices":[{"delta":{"content":"hi"}}]}', 'data: [DONE]']
    with patch.object(chat_engine, "_req") as mock_req:
        mock_req.post.return_value = _fake_stream_response(lines)
        list(stream_from_llm([{"role": "user", "content": "hi"}]))
    assert mock_req.post.call_count == 1
    _, kwargs = mock_req.post.call_args
    assert kwargs["json"]["stream"] is True
    assert kwargs["stream"] is True


def test_stream_from_llm_skips_unparseable_lines_and_blank_lines(temp_db):
    lines = [
        "",
        "event: ping",
        'data: {"choices":[{"delta":{"content":"ok"}}]}',
        "data: not json at all",
        'data: [DONE]',
    ]
    with patch.object(chat_engine, "_req") as mock_req:
        mock_req.post.return_value = _fake_stream_response(lines)
        chunks = list(stream_from_llm([{"role": "user", "content": "hi"}]))
    assert chunks == ["ok"]


def test_stream_from_llm_falls_back_to_non_streamed_on_connection_error(temp_db):
    fake_response = MagicMock()
    fake_response.json.return_value = {"choices": [{"message": {"content": "fallback reply"}}]}
    with patch.object(chat_engine, "_req") as mock_req:
        mock_req.post.side_effect = [ConnectionError("stream endpoint down"), fake_response]
        chunks = list(stream_from_llm([{"role": "user", "content": "hi"}]))
    assert "".join(chunks) == "fallback reply"
    assert mock_req.post.call_count == 2


def test_stream_from_llm_falls_back_when_server_sends_no_content(temp_db):
    """Server accepts stream=True but never sends a usable delta (e.g. streaming
    unsupported) -- must still produce a real reply via the non-streamed fallback."""
    fake_response = MagicMock()
    fake_response.json.return_value = {"choices": [{"message": {"content": "non-streamed reply"}}]}
    with patch.object(chat_engine, "_req") as mock_req:
        mock_req.post.side_effect = [_fake_stream_response(['data: [DONE]']), fake_response]
        chunks = list(stream_from_llm([{"role": "user", "content": "hi"}]))
    assert "".join(chunks) == "non-streamed reply"


def test_stream_from_llm_without_requests_library():
    with patch.object(chat_engine, "_req", None):
        chunks = list(stream_from_llm([{"role": "user", "content": "hi"}]))
    assert "not installed" in "".join(chunks)
