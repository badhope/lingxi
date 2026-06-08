# Security

## Reporting a vulnerability

Do not open a public issue.

Open a private advisory: <https://github.com/badhope/DATA-Agent/security/advisories/new>

Include:

- What the vulnerability is and how to reproduce it.
- What the impact looks like (data leak, RCE, etc.).
- A suggested fix if you have one.

You will get an acknowledgement within a few days.

## Things to keep in mind when deploying

- Never commit API keys. The project reads them from environment variables
  (`OPENAI_API_KEY`, etc.) — see `dataagent/config.py`.
- Rotate keys if you suspect they leaked. Revoke at
  <https://github.com/settings/tokens> and at your LLM provider.
- The default config binds the API to `0.0.0.0`. Put it behind a reverse proxy
  with auth if exposing it.
- The auth layer (`dataagent/core/auth.py`) uses PBKDF2. The default session
  TTL is fine for local use; tighten it for production.
