# weather

Ingest weather data from open APIs. Config-driven Python task runner using YAML to chain ingestion tasks.

## Quick start

```bash
uv sync --group dev
uv run pytest -q
uv run ruff check ./src ./tests
```

Install pre-commit hooks (optional):

```bash
uv run pre-commit install
```

## Project layout

```
src/
  runner.py          # TaskRunner — loads YAML, runs tasks in sequence
  tasks/
    base.py          # BaseTask interface
    registry.py      # @register_task decorator
    ingest/          # API ingestion tasks
tests/
docs/                # plans, brainstorms, solutions (compound engineering)
.cursor/             # agent rules, skills, hooks
```

## AI-assisted development

This repo uses a human-in-the-loop compound engineering workflow. See [docs/ai_assisted_development.md](docs/ai_assisted_development.md) for:

- **ce-plan** / **ce-work** / **ce-compound** skills
- Cursor ruff hooks (auto-lint after agent edits)
- Optional [RTK](https://www.rtk-ai.app/) setup for token-efficient agent shell commands

After cloning, restart Cursor and verify **Settings → Hooks** shows `afterFileEdit` and `stop`.

## Configuration

Example task config:

```yaml
tasks:
  - type: weather_api
    params:
      latitude: 45.123
      longitude: -73.456
      api_key: ${OPENWEATHER_API_KEY}
```

Never commit API keys — use environment variables.
