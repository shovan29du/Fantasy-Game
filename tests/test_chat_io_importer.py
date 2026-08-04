"""Import a chat log from a URL (chat_io/importer.py's import_chat_url).

Network calls are mocked. Verifies JSON/plain-text parsing, scheme
validation, and local-only mode enforcement.
"""
from unittest.mock import patch, MagicMock

from chat_io.importer import import_chat_url
from core.storage import set_bool_setting


def _fake_response(json_data=None, text=None, content_type="application/json"):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.headers = {"Content-Type": content_type}
    if json_data is not None:
        resp.json.return_value = json_data
    if text is not None:
        resp.text = text
    return resp


def test_import_chat_url_parses_json_message_list(temp_db):
    data = [{"speaker": "User", "text": "hi"}, {"speaker": "Bot", "text": "hello"}]
    with patch("chat_io.importer._req") as mock_requests:
        mock_requests.get.return_value = _fake_response(json_data=data)
        chat = import_chat_url("https://example.com/chat.json")
    assert len(chat) == 2
    assert chat[0]["speaker"] == "User"
    assert chat[1]["text"] == "hello"


def test_import_chat_url_parses_json_with_messages_key(temp_db):
    data = {"messages": [{"role": "user", "content": "hi there"}]}
    with patch("chat_io.importer._req") as mock_requests:
        mock_requests.get.return_value = _fake_response(json_data=data)
        chat = import_chat_url("https://example.com/log")
    assert len(chat) == 1
    assert chat[0]["text"] == "hi there"


def test_import_chat_url_parses_plain_text(temp_db):
    with patch("chat_io.importer._req") as mock_requests:
        mock_requests.get.return_value = _fake_response(
            text="Alice: hello there\nBob: hi Alice", content_type="text/plain")
        chat = import_chat_url("https://example.com/chat.txt")
    assert len(chat) == 2
    assert chat[0]["speaker"] == "Alice"
    assert chat[1]["speaker"] == "Bob"


def test_import_chat_url_rejects_non_http_scheme(temp_db):
    try:
        import_chat_url("file:///etc/passwd")
        assert False, "should have raised"
    except ValueError as e:
        assert "http" in str(e)


def test_import_chat_url_respects_local_only_mode(temp_db):
    set_bool_setting("local_only_mode", True)
    with patch("chat_io.importer._req") as mock_requests:
        try:
            import_chat_url("https://example.com/chat.json")
            assert False, "should have raised"
        except RuntimeError as e:
            assert "Local-only mode" in str(e)
    mock_requests.get.assert_not_called()
