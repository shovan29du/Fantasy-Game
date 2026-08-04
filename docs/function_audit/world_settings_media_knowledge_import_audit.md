# World Settings Media Knowledge Import Audit

## World Features Ported
- World create/load/detail, ticks, map locations, NPCs, factions, dungeons, combat, resources, laws, diplomacy, random events, timeline, weather, and campaign saves.

## Media Features Ported
- Gallery list/save/delete, providers, image generation, queued video/batch jobs, achievements, memory snapshots, and manual media registration.

## Knowledge Features Ported
- Search, upload/index file, index folder, regenerate character options doc, documents list/delete, lorebook create/list/toggle/delete, and D&D/options display.

## Settings Features Ported
- Dashboard counts, import test, DB integrity check, model selection, config values/toggles, backups, companion soul view, and system prompt editor.

## Architecture
- React/Vite-style static frontend remains served by FastAPI.
- Streamlit imports/runners/app folders were not restored.
