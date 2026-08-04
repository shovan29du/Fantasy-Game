# Frontend Migration

Streamlit has been fully replaced in the packaged app.

## Current frontend

- Default frontend: bundled React-style static UI at `frontend/react_app/dist/index.html`.
- The bundled UI follows the old AiChat Pro sidebar/page design while staying on React/FastAPI.
- Default backend: FastAPI app at `backend.app.main:app`.
- Default URL: `http://localhost:8501`.

## Development direction

Use React + Vite + TypeScript for continued frontend work. The existing `frontend/react_app/src` folder is the source workspace, while `dist` is bundled for users who do not have Node installed.

## No Streamlit

Do not add Streamlit back. Any old feature should be ported into FastAPI routes/services and React UI.
