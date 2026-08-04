# Character And Explore Import Audit

## Character Features Ported
- Single character creator with identity, appearance, measurements, combat, stats, personality, tags, story fields, JSON import/export, randomize, and photo generation.
- Multi-character creator up to 10 characters with group tag/scenario and save-all flow.
- Full database save uses the old broad character field set instead of the earlier minimal save.

## Explore Features Ported
- My Characters cards with search, tag filter, chat, export, photo, and delete actions.
- Library search/filter/import and import-all through FastAPI.
- chub.ai public companion search with full-card import fallback.
- General web search API route using the existing Brave/web-search core.
- Create Scenario remains merged into Explore per user request.

## Architecture
- No Streamlit module or UI folder restored.
- Features are exposed as stable FastAPI routes and consumed by React.
