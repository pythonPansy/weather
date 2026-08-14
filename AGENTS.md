# AGENTS.md

This repository is a config-driven Python (3.11+) project managed by `uv`. It contains
a **Weather App REST API** (FastAPI, SQLite-backed, the primary product) and a
**config-driven batch task runner** CLI. Standard setup, build, test, and run commands
are documented in `README.md` and `CONTRIBUTING.md`; follow those as the source of truth.

## Cursor Cloud specific instructions

The dependency-refresh step (`uv sync --group dev`) runs automatically on VM startup via
the environment update script. The notes below cover non-obvious, durable caveats for
running and testing services in this environment; they are not a substitute for
`README.md`/`CONTRIBUTING.md`.

### Services

- **Weather App API (primary)** — `src/weather/main.py`, FastAPI on port `8001`. This is
  the DB-backed service preferred for the Tight Lines integration. Start with
  `uv run uvicorn src.weather.main:app --reload --port 8001`.
  - It reads config from a `.env` file (gitignored). Copy `.env.example` to `.env`.
    `.env.example` defaults `TIDE_DATA_SOURCE` to `admiralty_discovery`, which needs a
    live `ADMIRALTY_API_KEY`. For offline development/testing set
    `TIDE_DATA_SOURCE=fixture` — the API then serves deterministic fixture tide data with
    no external API calls or keys required, and is fully exercisable end to end.
  - On startup the app auto-creates SQLite tables and seeds tide locations, so
    `GET /api/locations` returns data immediately. Running `uv run alembic upgrade head`
    first is still recommended (matches the README) and is harmless if tables already
    exist. The SQLite file `weather.db` is created in the repo root at runtime — do not
    commit it.
  - Endpoints: `GET /health`, `GET /api/locations`, `GET /api/tides/{location_id}`
    (query params `start`/`end` in ISO 8601). Interactive docs at `/docs`.
- **Legacy YAML-backed API** (`src/api/main.py`, optional) — same endpoint shapes but no
  DB/fixtures; `/api/tides` calls the live TideTurtle API, so it needs network access.
- **Batch task runner** (`python -m src config/pipeline.yaml`, optional) — one-shot CLI
  that hits live OpenWeatherMap/TideTurtle APIs and needs `OPENWEATHER_API_KEY`.

### Testing

- `uv run pytest -q` runs the full suite offline. Live-API tests are excluded by default
  (`addopts = -m 'not live_api'`); opt in with `uv run pytest -m live_api` only when the
  relevant API keys are available.

### Notes

- The `.cursor/rules` reference an `rtk` wrapper for shell commands; `rtk` is **not**
  installed in this cloud environment. Run the underlying commands directly
  (e.g. `uv run pytest`, `git ...`); `rtk` is a token-saving convenience, not required.
