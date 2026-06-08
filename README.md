# data-agent

FastAPI + CrewAI multi-agent data assistant.

[English](./README.md) | [中文](./README_zh.md)

## What it does

Two endpoints exposed by `dataagent.main`:

- `POST /api/analyze` — runs a 3-agent CrewAI flow (researcher → analyst → writer) on a user query
- `POST /api/knowledge/query` — runs a single knowledge-manager agent

There is also a `python -m dataagent.cli` interactive shell for the same two flows.

The rest of the code (`core/`, `routers/`, `app/`, `services/`) is the supporting layer:
auth, knowledge base, settings, conversations, websocket, workspace files, etc.

## Run

```bash
cd dataagent
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
python main.py            # API on :8000
# or
python cli.py             # interactive shell
```

Docs UI: <http://localhost:8000/docs>
Health: <http://localhost:8000/health>

## Layout

```
dataagent/
├── main.py            # FastAPI entry
├── cli.py             # CLI entry
├── config.py          # pydantic-settings, env-driven
├── core/              # config, db, auth, knowledge, websocket, workspace, logging
├── routers/           # FastAPI routes
├── services/          # document service, polish service
├── agents/            # CrewAI agent factories
├── crews/             # CrewAI crew definitions
├── app/knowledge/     # lightweight KB used by routers/knowledge.py
├── config/            # example TOML/JSON configs
├── static/            # frontend assets (not currently served by main.py)
└── templates/         # placeholder index.html
```

## Configuration

Settings come from environment variables (see `dataagent/config.py`) and from
optional TOML files in `config/`. Provider examples are in
`config/config.example-model-*.toml`.

## Notes

- The frontend in `static/` and `templates/` is not wired up to `main.py` yet.
  API consumers should hit the JSON endpoints directly.
- Most "advanced" features in the codebase (browser automation, MCP, multi-modal
  extensions, agent market) are scaffold-only. The two endpoints above are
  what actually works end-to-end.

## License

MIT
