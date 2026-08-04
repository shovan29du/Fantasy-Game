import json
import os

import pytest

os.environ.setdefault("RELAY_PORT", "5000")

import app as relay_app
import auth
import db
import migrations


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.reset_conn()
    db.init_db()
    auth.reset_cache()
    monkeypatch.setattr(relay_app, "CONFIG_PATH", str(tmp_path / "config.json"))
    relay_app._cooldowns.clear()
    relay_app._free_cache.update(ids=set(), at=0)
    relay_app._chat_hits.clear()
    relay_app.app.config["TESTING"] = True
    with relay_app.app.test_client() as c:
        yield c
    db.reset_conn()
    auth.reset_cache()


# ---- identity / no-login ----------------------------------------------------
def test_health_endpoint_is_unauthenticated_and_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.get_json()
    assert body["ok"] is True


def test_routes_reachable_with_no_login_step(client):
    """There is no sign-in screen and no auth route: every API route just
    works against the single implicit local user."""
    for path in ("/api/settings", "/api/models", "/api/conversations"):
        r = client.get(path)
        assert r.status_code == 200, path
    r = client.post("/api/chat", json={"conversationId": "x", "content": "hi"})
    assert r.status_code == 404  # no such conversation, but no auth gate either


def test_topbar_has_model_and_tool_dropdown_controls(client):
    with open(os.path.join(relay_app.APP_DIR, "templates", "index.html"), encoding="utf-8") as f:
        html = f.read()
    topbar = html.split('<div class="topbar">', 1)[1].split('<div class="main-body">', 1)[0]
    assert 'id="onlineModelSelect"' in topbar
    assert 'id="lmModelSelect"' in topbar
    assert 'id="agentBtn"' in topbar
    assert 'id="appsBtn"' in topbar
    assert 'id="pluginsBtn"' in topbar
    assert html.index('id="onlineModelSelect"') < html.index('<div class="composer-row1">')
    assert 'class="toolbar-row" style="display:none"' in html


def test_single_user_is_auto_provisioned_once(client):
    assert client.get("/api/settings").status_code == 200
    user = db.get_user_by_username(auth.DIRECT_ENTRY_USERNAME)
    assert user is not None
    # A second request reuses the same user instead of creating another.
    assert client.get("/api/settings").status_code == 200
    assert db.get_user_by_username(auth.DIRECT_ENTRY_USERNAME)["id"] == user["id"]


def test_no_auth_or_admin_routes_remain(client):
    for path in ("/api/auth/login", "/api/auth/register", "/api/auth/me",
                 "/api/admin/users", "/api/admin/stats"):
        assert client.get(path).status_code == 404, path


# ---- settings -----------------------------------------------------------------
def test_settings_roundtrip_and_key_not_echoed(client):
    r = client.post("/api/settings", json={"key": "sk-test", "temp": 0.5})
    assert r.status_code == 200
    cfg = client.get("/api/settings").get_json()
    assert cfg["has_key"] is True
    assert "key" not in cfg
    assert cfg["temp"] == 0.5


def test_settings_temp_clamped(client):
    client.post("/api/settings", json={"temp": 99})
    cfg = client.get("/api/settings").get_json()
    assert cfg["temp"] == 2.0


def test_models_endpoint_without_key(client):
    r = client.get("/api/models")
    assert r.status_code == 200
    d = r.get_json()
    assert d["has_key"] is False
    assert len(d["curated"]) == len(relay_app.CURATED)


# ---- conversations --------------------------------------------------------------
def test_create_list_rename_delete_conversation(client):
    r = client.post("/api/conversations", json={"title": "Hello"})
    assert r.status_code == 201
    conv = r.get_json()
    conv_id = conv["id"]

    listed = client.get("/api/conversations").get_json()["conversations"]
    assert any(c["id"] == conv_id for c in listed)

    r = client.patch(f"/api/conversations/{conv_id}", json={"title": "Renamed"})
    assert r.status_code == 200
    assert r.get_json()["title"] == "Renamed"

    r = client.delete(f"/api/conversations/{conv_id}")
    assert r.status_code == 200
    assert client.get(f"/api/conversations/{conv_id}").status_code == 404


def test_conversation_owned_by_other_user_is_not_visible(client):
    """The data layer still scopes conversations by user_id (used internally
    for FK integrity); this checks that scoping still works even though
    there's no API to create a second user anymore."""
    conv_id = db.create_conversation(db.create_user("other", "x"), "Other's chat")
    assert client.get(f"/api/conversations/{conv_id}").status_code == 404
    assert client.delete(f"/api/conversations/{conv_id}").status_code == 404
    assert client.patch(f"/api/conversations/{conv_id}", json={"title": "x"}).status_code == 404


def test_chat_persists_user_and_assistant_messages(client, monkeypatch):
    conv = client.post("/api/conversations", json={"title": "t"}).get_json()
    conv_id = conv["id"]

    def fake_order(selected, cfg):
        return [{"id": "fake/model", "name": "Fake", "provider": "openrouter", "available": True}]

    def fake_stream(model, messages, cfg):
        yield "Hello "
        yield "world"

    monkeypatch.setattr(relay_app, "build_order", fake_order)
    monkeypatch.setattr(relay_app, "stream_upstream", fake_stream)

    r = client.post("/api/chat", json={"conversationId": conv_id, "content": "hi there"})
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "Hello " in body and "world" in body

    detail = client.get(f"/api/conversations/{conv_id}").get_json()
    msgs = detail["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert msgs[0]["content"] == "hi there"
    assert msgs[1]["content"] == "Hello world"
    assert msgs[1]["model"] == "fake/model"


def test_chat_rejects_missing_conversation(client):
    r = client.post("/api/chat", json={"conversationId": "missing", "content": "hi"})
    assert r.status_code == 404


def test_chat_rejects_empty_content(client):
    conv = client.post("/api/conversations", json={"title": "t"}).get_json()
    r = client.post("/api/chat", json={"conversationId": conv["id"], "content": "   "})
    assert r.status_code == 400


def test_chat_rejects_oversized_message(client):
    conv = client.post("/api/conversations", json={"title": "t"}).get_json()
    r = client.post("/api/chat", json={
        "conversationId": conv["id"],
        "content": "x" * (relay_app.MAX_MESSAGE_CHARS + 1),
    })
    assert r.status_code == 400


def test_chat_rate_limit(client, monkeypatch):
    monkeypatch.setattr(relay_app, "CHAT_RATE_LIMIT", 1)
    conv = client.post("/api/conversations", json={"title": "t"}).get_json()

    def fake_order(selected, cfg):
        return []

    monkeypatch.setattr(relay_app, "build_order", fake_order)
    r1 = client.post("/api/chat", json={"conversationId": conv["id"], "content": "hi"})
    assert r1.status_code == 200
    r2 = client.post("/api/chat", json={"conversationId": conv["id"], "content": "hi again"})
    assert r2.status_code == 429


def test_chat_exhausted_with_no_models(client, monkeypatch):
    monkeypatch.setattr(relay_app, "CURATED", [])
    monkeypatch.setattr(relay_app, "detect_ollama", lambda url: [])
    conv = client.post("/api/conversations", json={"title": "t"}).get_json()
    r = client.post("/api/chat", json={"conversationId": conv["id"], "content": "hi"})
    body = r.get_data(as_text=True)
    assert "exhausted" in body


# ---- pure logic -----------------------------------------------------------------
def test_classify_ratelimit():
    err = relay_app.UpstreamError(429, "rate limited")
    assert relay_app.classify(err) == "ratelimit"


def test_classify_unavailable():
    err = relay_app.UpstreamError(503, "no instances available")
    assert relay_app.classify(err) == "unavailable"


def test_classify_other():
    err = relay_app.UpstreamError(400, "bad request")
    assert relay_app.classify(err) == "other"


def test_build_order_puts_selected_first():
    cfg = {"key": "", "ollama": "", "lm_studio": "", "system": "", "temp": 0.7}
    selected = relay_app.CURATED[2]["id"]
    order = relay_app.build_order(selected, cfg)
    assert order[0]["id"] == selected


# ---- migrations --------------------------------------------------------------
def test_migrations_are_idempotent(tmp_path, monkeypatch):
    db_path = str(tmp_path / "migrate.db")
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.reset_conn()
    db.init_db()
    conn = db.get_conn()
    versions_first = {r["version"] for r in conn.execute("SELECT version FROM schema_version").fetchall()}
    # Re-running init_db must not error and must not re-apply anything.
    db.init_db()
    versions_second = {r["version"] for r in conn.execute("SELECT version FROM schema_version").fetchall()}
    assert versions_first == versions_second
    assert versions_first == {v for v, *_ in migrations.MIGRATIONS}
    db.reset_conn()


def test_migration_upgrades_pre_existing_sqlite_db(tmp_path, monkeypatch):
    """A database created by the old single-migration schema (no is_admin
    column, no usage_events table) must upgrade in place instead of breaking."""
    import sqlite3 as _sqlite3

    db_path = str(tmp_path / "legacy.db")
    legacy_conn = _sqlite3.connect(db_path)
    legacy_conn.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at REAL NOT NULL
        );
        CREATE TABLE settings (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            api_key TEXT NOT NULL DEFAULT '',
            ollama TEXT NOT NULL DEFAULT '',
            system_prompt TEXT NOT NULL DEFAULT '',
            temperature REAL NOT NULL DEFAULT 0.7
        );
        """
    )
    legacy_conn.execute(
        "INSERT INTO users (username, password_hash, created_at) VALUES ('legacy', 'x', 0)"
    )
    legacy_conn.commit()
    legacy_conn.close()

    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.reset_conn()
    db.init_db()  # should not raise, and should add the missing columns/tables
    row = db.get_user_by_username("legacy")
    assert row["is_admin"] == 0  # new column backfilled with default
    db.record_usage(row["id"], None, None, 10, 2)  # new table now exists
    db.reset_conn()


# ---- usage tracking ---------------------------------------------------------------
def test_usage_summary_reachable_without_login(client):
    assert client.get("/api/usage/summary").status_code == 200


def test_usage_tracked_after_chat(client, monkeypatch):
    conv = client.post("/api/conversations", json={"title": "t"}).get_json()

    def fake_order(selected, cfg):
        return [{"id": "fake/model", "name": "Fake", "provider": "openrouter", "available": True}]

    def fake_stream(model, messages, cfg):
        yield "hello"

    monkeypatch.setattr(relay_app, "build_order", fake_order)
    monkeypatch.setattr(relay_app, "stream_upstream", fake_stream)
    r = client.post("/api/chat", json={"conversationId": conv["id"], "content": "hi there"})
    r.get_data()  # drain the SSE generator so persistence/usage recording runs

    summary = client.get("/api/usage/summary").get_json()["days"]
    assert len(summary) == 1
    assert summary[0]["messages"] == 2  # one user event, one assistant event
    assert summary[0]["chars"] > 0


# ---- API hardening ---------------------------------------------------------------
def test_chat_rejects_non_json_content_type(client):
    conv = client.post("/api/conversations", json={"title": "t"}).get_json()
    r = client.post(
        f"/api/chat",
        data=json.dumps({"conversationId": conv["id"], "content": "hi"}),
        content_type="text/plain",
    )
    assert r.status_code == 415
    assert r.get_json()["error"]["code"] == 415


def test_error_responses_have_structured_shape_and_request_id(client):
    r = client.get("/api/does-not-exist")
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"]["message"]
    assert body["error"]["code"] == 404
    assert body["requestId"]
    assert r.headers.get("X-Request-Id") == body["requestId"]


def test_unknown_route_returns_structured_404(client):
    r = client.get("/api/does-not-exist")
    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == 404


# ---- network-level token gate ---------------------------------------------------
def test_non_loopback_without_token_rejected(client, monkeypatch):
    monkeypatch.setattr(relay_app, "ACCESS_TOKEN", "")
    r = client.get("/api/health", environ_overrides={"REMOTE_ADDR": "10.0.0.5"})
    assert r.status_code == 401


def test_non_loopback_with_correct_token_allowed(client, monkeypatch):
    monkeypatch.setattr(relay_app, "ACCESS_TOKEN", "secret")
    r = client.get(
        "/api/health",
        environ_overrides={"REMOTE_ADDR": "10.0.0.5"},
        headers={"X-Relay-Token": "secret"},
    )
    assert r.status_code == 200


def test_non_loopback_with_new_header_name_allowed(client, monkeypatch):
    monkeypatch.setattr(relay_app, "ACCESS_TOKEN", "secret")
    r = client.get(
        "/api/health",
        environ_overrides={"REMOTE_ADDR": "10.0.0.5"},
        headers={"X-Ark-Ai-Token": "secret"},
    )
    assert r.status_code == 200


# ---- persistent memory -------------------------------------------------------
def test_memory_starts_empty_and_can_be_cleared(client):
    assert client.get("/api/memory").get_json()["facts"] == []
    user_id = auth.get_user_id()
    db.add_memory_facts(user_id, ["likes coffee", "works in Berlin"])
    facts = client.get("/api/memory").get_json()["facts"]
    assert facts == ["likes coffee", "works in Berlin"]
    r = client.delete("/api/memory")
    assert r.status_code == 200
    assert client.get("/api/memory").get_json()["facts"] == []


def test_memory_context_injects_recalled_facts(client):
    user_id = auth.get_user_id()
    db.add_memory_facts(user_id, ["loves dogs"])
    ctx = relay_app.memory_context(user_id)
    assert "loves dogs" in ctx


# ---- document upload / Q&A ---------------------------------------------------
def test_upload_extract_list_and_delete_doc(client):
    data = {"file": (__import__("io").BytesIO(b"hello world from a test file"), "notes.txt")}
    r = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert r.status_code == 200
    body = r.get_json()
    assert body["name"] == "notes.txt"
    fid = body["id"]

    listed = client.get("/api/docs").get_json()
    assert any(d["id"] == fid for d in listed)

    r = client.delete(f"/api/docs/{fid}")
    assert r.status_code == 200
    listed = client.get("/api/docs").get_json()
    assert not any(d["id"] == fid for d in listed)


def test_upload_rejects_missing_file(client):
    r = client.post("/api/upload", data={}, content_type="multipart/form-data")
    assert r.status_code == 400


def test_docs_are_scoped_to_uploading_user(client):
    data = {"file": (__import__("io").BytesIO(b"secret content"), "private.txt")}
    fid = client.post("/api/upload", data=data, content_type="multipart/form-data").get_json()["id"]
    other_user_id = "some-other-user"
    assert relay_app.docs_context(other_user_id, [fid]) == ""
    own_user_id = auth.get_user_id()
    assert "secret content" in relay_app.docs_context(own_user_id, [fid])


# ---- web search / research mode (network calls mocked) -----------------------
def test_search_context_formats_results(monkeypatch):
    def fake_search(query, max_results=5):
        return [{"title": "Result", "href": "http://example.com", "body": "a snippet"}]

    monkeypatch.setattr(relay_app, "web_search", fake_search)
    ctx = relay_app.search_context("test query")
    assert "test query" in ctx
    assert "example.com" in ctx


def test_search_context_empty_when_no_results(monkeypatch):
    monkeypatch.setattr(relay_app, "web_search", lambda q, max_results=5: [])
    assert relay_app.search_context("nothing") == ""


def test_chat_with_search_mode_injects_context(client, monkeypatch):
    conv = client.post("/api/conversations", json={"title": "t"}).get_json()

    def fake_order(selected, cfg):
        return [{"id": "fake/model", "name": "Fake", "provider": "openrouter", "available": True}]

    captured = {}

    def fake_stream(model, messages, cfg):
        captured["messages"] = messages
        yield "ok"

    monkeypatch.setattr(relay_app, "build_order", fake_order)
    monkeypatch.setattr(relay_app, "stream_upstream", fake_stream)
    monkeypatch.setattr(relay_app, "search_context", lambda q: "[Web search: weather]\nsome result")

    r = client.post("/api/chat", json={
        "conversationId": conv["id"], "content": "what's the weather",
        "mode": "search", "searchQuery": "weather",
    })
    r.get_data()
    assert any(m["role"] == "system" and "weather" in m["content"] for m in captured["messages"])


# ---- image / animation generation (network + Pillow calls mocked) ------------
def test_image_generation_requires_prompt(client):
    r = client.post("/api/image", json={"prompt": ""})
    assert r.status_code == 400


def test_image_generation_returns_media_url(client, monkeypatch):
    monkeypatch.setattr(relay_app, "generate_image_bytes", lambda prompt, **kw: b"fake-jpeg-bytes")
    r = client.post("/api/image", json={"prompt": "a red fox in snow"})
    d = r.get_json()
    assert r.status_code == 200
    assert d["url"].startswith("/api/media/")

    media = client.get(d["url"])
    assert media.status_code == 200
    assert media.data == b"fake-jpeg-bytes"
    assert media.mimetype == "image/jpeg"


def test_animation_generation_returns_media_url(client, monkeypatch):
    monkeypatch.setattr(relay_app, "generate_animation_bytes", lambda prompt, **kw: b"fake-gif-bytes")
    r = client.post("/api/animation", json={"prompt": "clouds drifting over mountains"})
    d = r.get_json()
    assert r.status_code == 200

    media = client.get(d["url"])
    assert media.data == b"fake-gif-bytes"
    assert media.mimetype == "image/gif"


def test_media_endpoint_404s_for_unknown_id(client):
    r = client.get("/api/media/doesnotexist")
    assert r.status_code == 404


def test_image_generation_failure_is_handled(client, monkeypatch):
    def boom(prompt, **kw):
        raise RuntimeError("upstream down")
    monkeypatch.setattr(relay_app, "generate_image_bytes", boom)
    r = client.post("/api/image", json={"prompt": "anything"})
    assert r.status_code == 502


# ---- direct Claude / DeepSeek providers and sandboxed code agent -------------
def test_models_hide_claude_and_deepseek_without_keys(client):
    d = client.get("/api/models").get_json()
    assert d["claude"] == []
    assert d["deepseek"] == []
    assert d["has_anthropic_key"] is False
    assert d["has_deepseek_key"] is False


def test_settings_persist_anthropic_and_deepseek_keys(client):
    client.post("/api/settings", json={"anthropicKey": "sk-ant-test", "deepseekKey": "sk-ds-test"})
    d = client.get("/api/models").get_json()
    assert d["has_anthropic_key"] is True
    assert d["has_deepseek_key"] is True
    assert len(d["claude"]) == len(relay_app.CLAUDE_MODELS)
    assert len(d["deepseek"]) == len(relay_app.DEEPSEEK_MODELS)
    settings = client.get("/api/settings").get_json()
    assert settings["has_anthropic_key"] is True
    assert settings["has_deepseek_key"] is True


def test_exec_code_tool_is_sandboxed_to_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(relay_app, "WORKSPACE_DIR", str(tmp_path))
    out = relay_app.exec_code_tool("write_file", {"path": "hello.txt", "content": "hi there"})
    assert "wrote" in out
    assert (tmp_path / "hello.txt").read_text() == "hi there"

    out = relay_app.exec_code_tool("read_file", {"path": "hello.txt"})
    assert out == "hi there"

    out = relay_app.exec_code_tool("list_files", {})
    assert "hello.txt" in out

    out = relay_app.exec_code_tool("read_file", {"path": "../../etc/passwd"})
    assert out.startswith("error:")


def test_run_code_agent_anthropic_executes_tool_then_answers(monkeypatch):
    calls = {"n": 0}

    def fake_post(url, headers=None, json=None, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            body = {"content": [{"type": "tool_use", "id": "t1", "name": "write_file",
                                  "input": {"path": "out.txt", "content": "done"}}]}
        else:
            body = {"content": [{"type": "text", "text": "Wrote the file."}]}
        return _FakeResp(200, body)

    monkeypatch.setattr(relay_app.requests, "post", fake_post)
    monkeypatch.setattr(relay_app, "exec_code_tool", lambda name, args: "ok")
    cfg = {"anthropic_key": "k", "system": ""}
    reply = relay_app.run_code_agent("anthropic", "claude-sonnet-4-6",
                                      [{"role": "user", "content": "write a file"}], cfg)
    assert reply == "Wrote the file."
    assert calls["n"] == 2


def test_run_code_agent_openai_executes_tool_then_answers(monkeypatch):
    calls = {"n": 0}

    def fake_post(url, headers=None, json=None, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            msg = {"role": "assistant", "tool_calls": [
                {"id": "c1", "function": {"name": "list_files", "arguments": "{}"}}]}
        else:
            msg = {"role": "assistant", "content": "Here are the files."}
        return _FakeResp(200, {"choices": [{"message": msg}]})

    monkeypatch.setattr(relay_app.requests, "post", fake_post)
    monkeypatch.setattr(relay_app, "exec_code_tool", lambda name, args: "a.txt\nb.txt")
    cfg = {"deepseek_key": "k", "system": ""}
    reply = relay_app.run_code_agent("deepseek", "deepseek-chat",
                                      [{"role": "user", "content": "list files"}], cfg)
    assert reply == "Here are the files."
    assert calls["n"] == 2


class _FakeResp:
    def __init__(self, status, body):
        self.status_code = status
        self.ok = status < 400
        self._body = body

    def json(self):
        return self._body


def test_chat_code_mode_without_keys_errors(client):
    conv = client.post("/api/conversations", json={"title": "t"}).get_json()
    r = client.post("/api/chat", json={"conversationId": conv["id"], "content": "fix this", "mode": "code"})
    raw = r.get_data(as_text=True)
    assert "LM Studio" in raw or "Claude" in raw


def test_chat_code_mode_runs_agent_and_persists_reply(client, monkeypatch):
    conv = client.post("/api/conversations", json={"title": "t"}).get_json()
    client.post("/api/settings", json={"deepseekKey": "sk-ds-test"})
    monkeypatch.setattr(relay_app, "stream_code_agent", lambda provider, model_id, history, cfg, **kw: iter([("answer", "All done.")]))
    r = client.post("/api/chat", json={"conversationId": conv["id"], "content": "fix this", "mode": "code"})
    raw = r.get_data(as_text=True)
    assert "All done." in raw
    msgs = client.get(f"/api/conversations/{conv['id']}").get_json()["messages"]
    assert msgs[-1]["content"] == "All done."
