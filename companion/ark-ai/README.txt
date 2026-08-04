============================================================
Ark_Ai  â€”  personal AI workspace
  No login. Pick from ~20 free models, automatic fallback.
============================================================

Ark_Ai (formerly "Realzip" / "Relay") is a small Python (Flask) web app.
There is no login system â€” it runs as a single local user, and
conversations/settings/API keys live in a local SQLite database.
You pick a model from a dropdown; if it's rate-limited, Ark_Ai
automatically relays your message to the next available model.
It uses OpenRouter's free models over the web, plus any local
models you run with Ollama.

Offline help included in this folder:
- INSTALL_HELP_ALL_OS.txt — installation and troubleshooting for Windows,
  macOS, Linux, and the universal Python installer.
- ARK_AI_USER_GUIDE.txt — complete feature guide, workflows, skills, commands,
  privacy guidance, and usage troubleshooting.


------------------------------------------------------------
RUNNING LOCALLY
------------------------------------------------------------
1. Create a virtual environment and install dependencies:
     python3 -m venv venv
     ./venv/bin/pip install -r requirements.txt
     # for running the test suite too:
     ./venv/bin/pip install -r requirements-dev.txt

2. Start the app:
     ./venv/bin/python app.py
   Your browser opens at  http://127.0.0.1:5000

3. The app opens straight into the chat UI â€” no sign-in step.
   Open Settings (gear icon) and paste a free OpenRouter API key.
   Get a key at  https://openrouter.ai/keys  (free, no card).

Windows users can double-click run_ark_ai.bat or run.bat from the
extracted folder. On first run, the launcher creates the virtual
environment, installs requirements.txt, initializes the database, and
starts Ark_Ai. The fuller install_ark_ai.bat / run_ark_ai.bat /
uninstall_ark_ai.bat flow is documented in README_INSTALL_WINDOWS.txt.

macOS users can extract the ZIP and double-click install_ark_ai.command.
If macOS blocks the first launch, Control-click it, choose Open, and confirm.
The installer creates the environment, database, and an Ark_Ai.command
launcher on the Desktop. It can also be run from Terminal with:
     bash install_ark_ai.command

Linux users can extract the ZIP, open a terminal in the folder, and run:
     chmod +x install_ark_ai.sh
     ./install_ark_ai.sh
The installer creates a virtual environment, initializes the database, and
creates an Ark_Ai.desktop launcher on the Desktop when available.

Universal fallback for Windows, macOS, and Linux:
     python full_install.py

To upgrade an existing Windows folder safely, extract the new zip to a
separate folder and run upgrade_ark_ai.bat from the new folder. It copies
new app files into the old folder while preserving .env, config.json,
ark_ai.db / realzip.db, workspace, and venv.


------------------------------------------------------------
ENVIRONMENT VARIABLES
------------------------------------------------------------
ARK_AI_PORT             Port to listen on. Default: 5000
ARK_AI_HOST             Bind address. Default: 127.0.0.1
                        Set to 0.0.0.0 only behind a trusted
                        proxy / when ARK_AI_TOKEN is also set.
ARK_AI_SECRET_KEY       Secret used to sign the Flask session
                        cookie. Set this to a fixed random value
                        so it doesn't change on every restart.
ARK_AI_TOKEN            Shared token required on every request
                        that does NOT originate from 127.0.0.1.
                        Leave unset to keep the server fully
                        local-only (recommended).
ARK_AI_DB_PATH          Path to the SQLite database file. Only
                        used when DATABASE_URL is unset.
                        Default: ark_ai.db next to app.py
DATABASE_URL            PostgreSQL connection string, e.g.
                        postgresql://user:pass@host:5432/ark_ai
                        When set, Ark_Ai uses PostgreSQL instead
                        of SQLite. Leave unset for SQLite (the
                        default, recommended for self-hosting).
ARK_AI_CHAT_RATE_LIMIT  Max /api/chat requests per user per
                        window. Default: 20
ARK_AI_CHAT_RATE_WINDOW Window length in seconds. Default: 60
OPENROUTER_API_KEY      Instance-wide fallback API key used only
                        when a user hasn't set their own key in
                        Settings.
ARK_AI_COOKIE_SECURE    Set to "1" to mark the session cookie
                        Secure (requires HTTPS). Default: "0"

(The old RELAY_* names above are still read as a fallback when the
corresponding ARK_AI_* variable is unset, so existing installs keep
working.)


------------------------------------------------------------
RUNNING TESTS
------------------------------------------------------------
     ./venv/bin/pip install -r requirements-dev.txt
     ./venv/bin/python -m pytest test_app.py -v

Tests cover settings persistence, conversation CRUD, message
persistence, the automatic-fallback chat logic, the non-loopback
token gate, schema migrations (including upgrading a pre-existing
legacy SQLite file in place), usage tracking, and API
error/content-type hardening. They run against a temporary SQLite
file and never touch your real ark_ai.db.


------------------------------------------------------------
DATABASE: SQLITE VS POSTGRESQL
------------------------------------------------------------
Ark_Ai ships with SQLite as the default backend â€” nothing to
install, the database is a single file (ARK_AI_DB_PATH). This is
the recommended setup for self-hosting and small deployments.

For a real multi-tenant cloud deployment, set DATABASE_URL to a
PostgreSQL connection string instead:

     export DATABASE_URL=postgresql://user:pass@host:5432/ark_ai
     ./venv/bin/pip install -r requirements-postgres.txt
     ./venv/bin/python app.py

When DATABASE_URL is set, Ark_Ai talks to PostgreSQL through
psycopg2 instead of sqlite3; ARK_AI_DB_PATH is then ignored. The
same code paths and schema migrations run against either backend
â€” db.py abstracts the two behind one `conn.execute(sql, params)`
call using `?` placeholders, so application code never branches
on which database is in use.

Note: PostgreSQL support is implemented and exercised by the
migration logic, but actual connections to a live PostgreSQL
server have not been integration-tested in this sandbox (no
PostgreSQL instance available here) â€” test it against a real
instance before relying on it in production.


------------------------------------------------------------
SCHEMA MIGRATIONS
------------------------------------------------------------
migrations.py defines a versioned, ordered list of migrations
(users/settings/conversations/messages, usage tracking, and a
couple of now-unused legacy columns/tables kept around so older
SQLite files upgrade in place without data loss). db.init_db() â€” called once at
startup â€” applies whatever hasn't been applied yet, tracked in
a `schema_version` table, so:

  - Running the app for the first time creates every table.
  - Upgrading an existing SQLite database created by an older
    Ark_Ai release only applies the migrations it's missing â€”
    existing users/conversations/messages are untouched.
  - Running init_db() twice in a row is a no-op the second time.

There is no separate "migrate" command to run â€” migrations apply
automatically every time the app starts.


------------------------------------------------------------
RUNNING WITH DOCKER
------------------------------------------------------------
     docker build -t ark_ai .
     docker run -p 5000:5000 \
       -e ARK_AI_SECRET_KEY=$(openssl rand -hex 32) \
       -e ARK_AI_TOKEN=$(openssl rand -hex 32) \
       -v ark_ai-data:/data \
       ark_ai

The container binds 0.0.0.0 by default (ARK_AI_HOST), so
ARK_AI_TOKEN is required or every non-loopback request will be
rejected with 401. The SQLite database lives in the /data
volume so it survives container restarts. Put a reverse proxy
with TLS in front of it for anything beyond local testing, and
set ARK_AI_COOKIE_SECURE=1 once HTTPS is in place.

To run against PostgreSQL instead, add -e DATABASE_URL=... â€” the
image already includes psycopg2-binary, so no rebuild is needed:

     docker run -p 5000:5000 \
       -e ARK_AI_SECRET_KEY=$(openssl rand -hex 32) \
       -e ARK_AI_TOKEN=$(openssl rand -hex 32) \
       -e DATABASE_URL=postgresql://user:pass@db-host:5432/ark_ai \
       ark_ai


------------------------------------------------------------
USING Ark_Ai
------------------------------------------------------------
- No sign-in step â€” the app opens straight into the chat UI.
- Model dropdown (top left): ~20 curated free models, tagged by
  strength (reasoning / coding / general / long ctx / fast /
  vision). Click "show all" to list every model that is free on
  OpenRouter right now.
- Automatic fallback: if your chosen model is busy, Ark_Ai moves
  to the next available one and shows a "Relayed to ..." note.
- Local models: install Ollama (https://ollama.com), pull a model
  (e.g.  ollama pull llama3.2 ), then click Detect in Settings.
  Local models have no rate limits.
- Conversations live in History (left sidebar): double-click to
  rename, hover to delete, or branch any message into a new chat.
- Installed skills: portable SKILL.md packages placed under
  skills/<skill-name>/SKILL.md appear automatically in the Agents panel.
  Selecting one adds its workflow instructions to that chat. Skill files are
  treated as instructions only; bundled scripts are never run automatically.


------------------------------------------------------------
WHERE THINGS ARE STORED
------------------------------------------------------------
- Settings, conversations, and messages: ark_ai.db (SQLite file
  next to app.py, or ARK_AI_DB_PATH). The API key is stored here
  and is never echoed back to the browser by /api/settings â€” only
  a has_key boolean is returned.
- config.json (legacy, optional): instance-wide fallback values
  used only when you haven't configured your own settings.
  Kept out of git via .gitignore.


------------------------------------------------------------
SECURITY NOTES
------------------------------------------------------------
- There is no login system. Anyone who can reach the server can
  use it as the single local user â€” access control is entirely
  the network-level gate below, not a per-user password.
- Network-level gate: any request not from 127.0.0.1 is rejected
  unless it carries a matching X-Ark-Ai-Token header (ARK_AI_TOKEN).
  Do not bind to 0.0.0.0 without setting ARK_AI_TOKEN.
- The API key is stored in SQLite, never returned to the frontend
  in plaintext after being saved.
- /api/chat validates conversation ownership, message length and
  count, and applies a rate limit (ARK_AI_CHAT_RATE_LIMIT per
  ARK_AI_CHAT_RATE_WINDOW seconds).
- Every API error returns a consistent JSON shape â€”
  {"error": {"message", "code"}, "requestId": "..."} â€” and every
  response carries an X-Request-Id header for tracing.
- Write routes (POST/PUT/PATCH) require Content-Type:
  application/json and reject anything else with 415.


------------------------------------------------------------
MIGRATION NOTES
------------------------------------------------------------
See "SCHEMA MIGRATIONS" above â€” migrations run automatically on
every app start via db.init_db(), are tracked in a schema_version
table, and are safe to re-run. No manual migration step is
required when upgrading to this version from an earlier Realzip/Relay
release; your existing SQLite file will be upgraded in place the
first time you start the new version.


------------------------------------------------------------
KNOWN PRODUCTION-READINESS GAPS
------------------------------------------------------------
- PostgreSQL support is implemented (DATABASE_URL, schema applied
  via the same migrations) but has not been integration-tested
  against a live PostgreSQL server in this environment.
- Usage tracking is per-request character/token estimates (not
  exact LLM token counts from the provider), intended for rough
  visibility rather than billing-grade accounting.
- In-memory rate limiting and model cooldowns reset on restart and
  don't share state across multiple app instances/workers â€” fine
  for a single-process deployment, not yet for horizontal scaling.
============================================================
