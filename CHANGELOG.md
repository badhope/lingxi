# Changelog

## Unreleased

### Changed
- Removed dead code: `app/document/*` (unwired summarizer/translator/PDF/PPT stack), unused frontend assets, `core/config_manager.py` (EnhancedConfigManager had no callers), and `requirements-minimal.txt` (conflicted with the main `requirements.txt`).
- Cleaned `core/__init__.py`, `routers/__init__.py`, `services/__init__.py` so they only import what actually exists.
- Rewrote docs to match what the code does, not what an older version promised.

### Notes
- Only `POST /api/analyze` and `POST /api/knowledge/query` work end-to-end.
- `static/` and `templates/` are not served by `main.py`. They are kept for now in case someone wants to wire them up.

## Earlier

See git history. v1.x had Docker sandbox and an older multi-agent prototype; v2.0 cut most of that.
