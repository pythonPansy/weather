# Copilot / AI agent instructions for the `weather` repo

## Purpose

Config-driven Python pipeline to ingest weather data from open APIs. Default branch: `main`.

## Canonical guidance

For Cursor, prefer `.cursor/rules/cursor_instructions.mdc` and `docs/ai_assisted_development.md`. This file covers Copilot and general agent conventions.

## Current state

- Python 3.11+, **uv** package manager (`uv.lock`)
- `src/` — `TaskRunner`, `BaseTask`, task registry, `WeatherAPITask` in `src/tasks/ingest/`
- `tests/` — pytest unit tests
- `.cursor/` — compound engineering rules, skills, ruff hooks

## RTK (optional, recommended for agents)

[RTK](https://www.rtk-ai.app/) compresses shell output to save agent context tokens. **Do not** `pip install rtk` — that is a different package.

- Install rtk-ai per [official docs](https://www.rtk-ai.app/docs/getting-started/installation/)
- Global hook: `rtk init --global --agent cursor` then restart Cursor
- Prefer `rtk uv run pytest`, `rtk uv run ruff`, `rtk git diff` for agent shell commands
- On native Windows without WSL, prefix commands explicitly (auto-rewrite needs WSL)

## Repository conventions

- `src/` for runtime code, `tests/` for unit tests
- Dependencies in `pyproject.toml` only — do not add unpinned deps
- No secrets in repo — use environment variables for API keys
- Mock external APIs in tests; do not call live APIs without approval
- Feature branches off `main`: `feature/<short-desc>` or `fix/<short-desc>`
- Do not commit unless the user asks

## Validation commands

```bash
uv sync --group dev
rtk uv run ruff check ./src ./tests
rtk uv run pytest -q
```

## Compound engineering

Before non-trivial changes, use **ce-plan** to write `docs/plans/YYYY-MM-DD-<slug>.md` and wait for user approval before implementing. See `docs/ai_assisted_development.md`.

## References

- [README.md](../README.md)
- [docs/ai_assisted_development.md](../docs/ai_assisted_development.md)
- [NextSteps.md](../NextSteps.md) — learning roadmap
