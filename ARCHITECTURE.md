# AiChat Pro Architecture

AiChat Pro uses **FastAPI + React** as the application architecture. Streamlit has been fully removed from the packaged app.

## Default entrypoints

- `run_app.bat` starts `uvicorn backend.app.main:app` on `http://localhost:8501`.
- `run_app.sh` does the same on macOS/Linux.
- `frontend/react_app/dist/index.html` is bundled so the app opens without requiring a Node build.
- `full_install.py` installs required and optional Python packages, seeds knowledge, and creates shortcuts.

## Canonical layout

```text
backend/
  app/
    main.py              # FastAPI app and API routes
    core/                # Backend logic
    domain/              # Domain catalogs and rules
    services/            # Stable service boundary
    chat_io/             # Chat import/export backend helpers
    story/               # Narrative backend helpers
    world/               # World template backend helpers
    map_engine/          # Map/pathfinding backend helpers

frontend/
  react_app/
    dist/                # Bundled frontend served by FastAPI
    src/                 # React/Vite source for future development

shared/
  schemas/
```

## Rules

1. New UI work goes in `frontend/react_app`.
2. New backend behavior goes behind FastAPI routes or `backend/app/services`.
3. Do not add Streamlit dependencies or Streamlit UI files.
4. Legacy feature logic must be ported into FastAPI services and React pages, not restored as Streamlit.
