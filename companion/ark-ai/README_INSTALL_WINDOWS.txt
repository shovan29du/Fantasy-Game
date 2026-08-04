============================================================
  Ark_Ai - Windows Installer Guide
============================================================

This package adds a one-click install/run/uninstall flow for
Ark_Ai on Windows 10/11, on top of the existing Flask app. It
does not change app.py, db.py, auth.py, or migrations.py, and it
does not remove Docker/Linux support â€” Docker and the existing
README.txt setup still work exactly as before.

Files added by this package:
  install_ark_ai.bat          - one-time setup
  run_ark_ai.bat               - everyday launcher
  upgrade_ark_ai.bat           - upgrade an existing folder safely
  uninstall_ark_ai.bat         - removes shortcuts / venv / db
  create_shortcuts.ps1          - used by the installer to make shortcuts
  README_INSTALL_WINDOWS.txt    - this file
  .env.example                  - template for the local config file


------------------------------------------------------------
REQUIREMENTS
------------------------------------------------------------
- Windows 10 or 11
- Python 3.10+ installed and on PATH (get it from
  https://www.python.org/downloads/ - check "Add python.exe to
  PATH" during install)
- No administrator rights needed. Everything is installed under
  the project folder and your own user profile.


------------------------------------------------------------
INSTALLING
------------------------------------------------------------
1. Download/extract the Ark_Ai folder anywhere you like
   (Desktop, Documents, a USB drive â€” anywhere you have write
   access).
2. Double-click install_ark_ai.bat (or run it from a Command
   Prompt opened in that folder).
3. The installer will:
     - Detect Python (tries the `py` launcher, then `python`,
       then `python3`)
     - Create a virtual environment in .\venv
     - Install requirements.txt
     - Ask if you want developer/test dependencies
       (requirements-dev.txt, only needed to run pytest)
     - Ask if you want PostgreSQL instead of SQLite
       (installs requirements-postgres.txt and asks for
       DATABASE_URL if so â€” see the PostgreSQL section below)
     - Ask whether to run on localhost only (recommended) or
       expose it to your network
     - Generate a random ARK_AI_SECRET_KEY (and an ARK_AI_TOKEN, if
       you chose network exposure) and write them to a local
       .env file
     - Initialize the database (runs the same migrations.py
       logic the app uses on every start)
     - Create a Desktop shortcut (OneDrive Desktop if you have
       one â€” see below) and a Start Menu shortcut
4. When it finishes, it prints the URL to open.

You can re-run install_ark_ai.bat safely at any time â€” it skips
steps that are already done (existing venv, existing .env) and
only re-asks what's actually missing.


------------------------------------------------------------
UPGRADING
------------------------------------------------------------
To upgrade an existing Ark_Ai folder without losing local data:

1. Extract the new Ark_Ai zip to a separate folder.
2. Double-click upgrade_ark_ai.bat in the NEW folder.
3. When asked, enter the OLD/existing Ark_Ai folder path.

The upgrade helper backs up and preserves:
  - .env
  - config.json
  - ark_ai.db / realzip.db
  - workspace
  - venv

It copies the new app files over the old folder, restores preserved user
data, then runs dependency/database upgrade steps when the existing venv is
available. A timestamped _upgrade_backup_* folder is left in the old app
folder so you can recover local data if needed.


------------------------------------------------------------
RUNNING
------------------------------------------------------------
After installing, start Ark_Ai any of these ways:
  - Double-click the "Ark_Ai" shortcut on your Desktop
  - Double-click "Ark_Ai" in your Start Menu
  - Double-click run_ark_ai.bat directly in the project folder

You can also double-click run_ark_ai.bat first. If the virtual
environment is missing, it creates .\venv, installs requirements.txt,
initializes the database, then starts app.py. On later runs it reuses
the existing environment. The window stays open if the app crashes, so
you can read the error instead of it vanishing.

Your browser does not open automatically from the .bat launcher
(app.py's own auto-open only fires when ARK_AI_HOST is loopback
and nothing else is already listening on the port) â€” if it
doesn't open, browse to the URL printed by the installer
(usually http://127.0.0.1:5000).


------------------------------------------------------------
ONEDRIVE DESKTOP BEHAVIOR
------------------------------------------------------------
Many Windows + Microsoft 365 setups redirect your visible Desktop
folder into OneDrive (%USERPROFILE%\OneDrive\Desktop) instead of
the classic %USERPROFILE%\Desktop. The installer checks for the
OneDrive Desktop folder first:
  - If %USERPROFILE%\OneDrive\Desktop exists, the shortcut is
    created there (this is almost always the folder you actually
    see when OneDrive is in use).
  - Otherwise, it falls back to the regular
    %USERPROFILE%\Desktop.
A Start Menu shortcut is always created in addition, regardless
of which Desktop was used, so Ark_Ai is reachable through the
Start Menu search even if a Desktop shortcut isn't visible for
some reason (e.g. a non-standard OneDrive folder location).


------------------------------------------------------------
UNINSTALLING
------------------------------------------------------------
Run uninstall_ark_ai.bat. It will:
  1. Remove the Desktop shortcut (checks OneDrive Desktop and the
     normal Desktop)
  2. Remove the Start Menu shortcut
  3. Ask before deleting the .\venv virtual environment
  4. Ask before deleting local *.db SQLite file(s)
  5. Ask before deleting the local .env config
  6. NEVER deletes your project source code (app.py, db.py,
     templates\, etc.) unless you type DELETE at the final
     prompt â€” pressing Enter (or anything else) always keeps
     the source code.


------------------------------------------------------------
TROUBLESHOOTING
------------------------------------------------------------
"Python was not found"
  Install Python 3.10+ from python.org and make sure "Add
  python.exe to PATH" was checked. Re-run install_ark_ai.bat.

"virtual environment not found"
  Run install_ark_ai.bat before run_ark_ai.bat.

The installer or launcher window closes immediately
  These scripts always end with `pause`, so an immediate close
  usually means Windows blocked the script outright. Right-click
  the .bat file -> Properties -> if there's an "Unblock"
  checkbox near the bottom, check it and click OK, then try
  again.

Windows Defender / SmartScreen flags the .bat or .ps1 files
  These are plain-text batch/PowerShell scripts â€” open them in
  Notepad to read exactly what they do (no compiled binaries,
  no PyInstaller, no obfuscation). If SmartScreen still warns
  ("Windows protected your PC"), click "More info" then "Run
  anyway", or just open the README and inspect/run the scripts
  manually.

create_shortcuts.ps1 fails to run directly
  PowerShell's default execution policy blocks unsigned scripts.
  install_ark_ai.bat already calls it with
  `-ExecutionPolicy Bypass` for this one invocation only (it does
  not change your system-wide PowerShell policy). To run it by
  hand: powershell -ExecutionPolicy Bypass -File create_shortcuts.ps1

Port 5000 already in use / app won't start
  Edit .env and change ARK_AI_PORT to a free port (e.g. 5050).

I changed my mind about network exposure / ARK_AI_TOKEN
  Edit .env directly â€” ARK_AI_HOST, ARK_AI_TOKEN, ARK_AI_SECRET_KEY,
  and DATABASE_URL are all plain KEY=VALUE lines. Restart with
  run_ark_ai.bat to pick up the change.


------------------------------------------------------------
SECURITY NOTES
------------------------------------------------------------
- .env is generated locally by the installer and is listed in
  .gitignore â€” it is never committed and should never be shared,
  since it holds ARK_AI_SECRET_KEY and (if network mode was
  chosen) ARK_AI_TOKEN.
- Localhost-only mode (the default) means only this PC can reach
  Ark_Ai; no token is needed and none is generated.
- Network-exposed mode (0.0.0.0) requires ARK_AI_TOKEN â€” every
  request that doesn't come from 127.0.0.1 must present it via
  the X-Ark-Ai-Token header, matching the existing token-gate
  behavior described in README.txt. The installer generates a
  random token automatically if you don't supply your own.
- Per-user passwords, API keys, and conversations are still
  stored exactly as documented in README.txt (PBKDF2 password
  hashing, API keys never echoed to the browser, etc.) â€” this
  installer only automates getting the existing app running, it
  does not change its security model.
- The uninstaller asks before touching your database or .env, and
  never deletes source code without an explicit typed
  confirmation.


------------------------------------------------------------
POSTGRESQL OPTION
------------------------------------------------------------
By default Ark_Ai uses a local SQLite file (the same behavior
as on Linux/Docker). If you choose "Use PostgreSQL" during
installation:
  - requirements-postgres.txt (psycopg2-binary) is installed into
    the virtual environment
  - You're prompted for a DATABASE_URL, e.g.
      postgresql://user:pass@host:5432/ark_ai
  - It's written to .env and used for every future run
  - The same migrations.py logic that applies to SQLite applies
    to PostgreSQL â€” no separate setup step is needed beyond
    having a reachable PostgreSQL server and a valid
    DATABASE_URL
See README.txt's "DATABASE: SQLITE VS POSTGRESQL" section for
more detail on how the two backends are abstracted in db.py.


------------------------------------------------------------
WHAT THIS INSTALLER DOES NOT DO (YET)
------------------------------------------------------------
- It does not build a standalone .exe (no PyInstaller). This is
  intentionally a transparent batch/PowerShell installer so
  everything it does is plain text you can read before running.
- It does not register Ark_Ai to start automatically on Windows
  login â€” start it manually via the shortcut when you want to
  use it.
============================================================
QUICK INSTALL FROM THE ZIP
--------------------------
1. Extract the entire ZIP to a permanent folder.
2. Double-click install_ark_ai.bat, or run: python full_install.py
3. The installer creates Ark_Ai shortcuts on the normal Desktop, every
   detected OneDrive Desktop, and the current user's Start Menu.

