# AiChat Pro

A local-first AI companion, roleplay, character, and world-simulation platform.

## Quick Start

```bat
install_windows.bat
run_app.bat
```

Open `http://127.0.0.1:8501` if the browser does not open automatically.

## Architecture

- Frontend: React-style bundled UI in `frontend/react_app/dist`.
- Backend: FastAPI app in `backend/app/main.py`.
- Database: local SQLite under `data`.
- Installer: `full_install.py`.

Streamlit has been removed from the packaged app. Do not use or restore Streamlit files for new features.

## Key Features

- Old-style AiChat Pro sidebar design in React.
- Character creation with race, profession, background, magic, power, trait, quirk, skill, tag, emotion, and image-style options.
- Scenario creation merged into Explore with template save/load/delete and randomized character names.
- Knowledge files for app options and SRD-compatible D&D guide material.
- Backend support modules for chat import/export, story helpers, world templates, map/pathfinding, media, memory, quests, relationships, and storage.

## Run

Windows:

```bat
run_app.bat
```

macOS/Linux:

```bash
./run_app.sh
```

## Ark AI Companion (optional)

`companion/ark-ai` bundles **Ark AI**, a standalone Flask chat workspace that talks to
OpenRouter's free models, Ollama, and LM Studio, with its own SQLite database and
skill library. It runs as a second, independent local server (default
`http://127.0.0.1:5000`) and is not required for the main game.

The topbar and sidebar of the main app include an **⚡ Ark AI Companion** link that
opens this second server in a new tab when it is running.

To run it alongside the game:

```bash
cd companion/ark-ai
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python app.py
```

See `companion/ark-ai/README.txt` for the full install/run guide (Windows/macOS/Linux
scripts are included in that folder).
