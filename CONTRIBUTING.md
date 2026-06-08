# Contributing

PRs and merges go through review by the maintainer — no bot does it automatically.

## Setup

```bash
git clone https://github.com/badhope/DATA-Agent.git
cd DATA-Agent/dataagent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## Workflow

1. Branch from `main`: `git checkout -b <type>/<short-desc>`
   - `feat/...` new feature
   - `fix/...` bug
   - `chore/...` refactor / cleanup / docs
2. Make the change. Keep it focused.
3. Run the API and CLI locally to sanity-check.
4. Open a PR. Fill in the template. Reference the issue if any.
5. Maintainer reviews and merges.

## Style

- Python 3.10+. PEP 8, type hints where they help.
- Keep modules small. One router per file. Services do not import routers.
- Do not add docstrings that just repeat the function name. Do add a one-line
  docstring on every public function.
- Do not introduce new top-level config files; extend `dataagent/config.py` and
  `config/config.example.toml` if needed.

## Commit messages

```
<scope>: <imperative summary>

<body explaining why, not what>
```

## What to avoid

- New `requirements-minimal.txt` style files — there is exactly one `requirements.txt`.
- New "minimal" config shims next to the real ones.
- Frontend pages that the backend does not serve. Either wire them in `main.py`
  or don't add them.
- Auto-generated AI-style READMEs full of badges and emoji.
