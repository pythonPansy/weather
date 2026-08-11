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

## Run the pipeline

Set the OpenWeatherMap key (required for weather and forecast tasks), then:

```bash
export OPENWEATHER_API_KEY=…
uv run python -m src config/pipeline.yaml
```

This runs the tasks in `config/pipeline.yaml` in order. Whole-string `${VAR}` placeholders in YAML are expanded from the environment (missing or empty vars fail fast).

Default outputs (gitignored under `data/`):

| File | Source |
| ---- | ------ |
| `data/weather.parquet` | Current conditions (`/data/2.5/weather`) |
| `data/weather_forecast.parquet` | 5-day / 3-hour forecast (`/data/2.5/forecast`) |
| `data/tides.parquet` | TideTurtle tides |

Each Parquet export appends one row per run with `latitude`, `longitude`, `fetched_at`, and the full JSON `response`.

Never commit API keys or collected `data/` files.

## REST API

The weather app provides REST API endpoints for tide locations and predictions.

### Start the API server

```bash
uv run uvicorn src.api.main:app --reload --port 8001
```

The API will be available at `http://localhost:8001` with interactive documentation at `http://localhost:8001/docs`.

### API Endpoints

#### `GET /api/locations`

Returns all available tide locations.

**Example:**

```bash
curl http://localhost:8001/api/locations | jq
```

**Response:**

```json
[
  {
    "id": "plym-uk-001",
    "name": "Plymouth",
    "region": "South Devon",
    "latitude": 50.3755,
    "longitude": -4.1427
  },
  ...
]
```

#### `GET /api/tides/{location_id}`

Returns tide predictions for a specific location and date range.

**Query Parameters:**

- `start`: Start date/time in ISO 8601 format (e.g., `2026-08-11T00:00:00Z`)
- `end`: End date/time in ISO 8601 format (e.g., `2026-08-18T23:59:59Z`)

**Example:**

```bash
curl "http://localhost:8001/api/tides/plym-uk-001?start=2026-08-11T00:00:00Z&end=2026-08-18T23:59:59Z" | jq
```

**Response:**

```json
{
  "tides": [
    {
      "time": "2026-08-11T05:23:00Z",
      "type": "high",
      "height": 4.8,
      "phase": "spring"
    },
    {
      "time": "2026-08-11T11:42:00Z",
      "type": "low",
      "height": 1.2,
      "phase": "spring"
    },
    ...
  ]
}
```

**Tide Phase Classification:**

- `"spring"`: Spring tide (high tidal range)
- `"neap"`: Neap tide (low tidal range)
- `"medium"`: Medium tide (between spring and neap)
- `null`: Phase classification unavailable

### API Testing

Run API tests:

```bash
uv run pytest tests/api/ -q
```

Run API tests including live API calls:

```bash
uv run pytest tests/api/ -m live_api
```

## Project layout

```
src/
  __main__.py        # CLI: python -m src <config.yaml>
  runner.py          # TaskRunner — loads YAML, expands env, runs tasks
  context.py         # PipelineContext shared state
  api/
    main.py          # FastAPI application
    models.py        # Pydantic models (Location, TideEvent, etc.)
    services.py      # Business logic for locations and tides
  tasks/
    base.py          # BaseTask interface
    registry.py      # @register_task decorator
    ingest/          # API ingestion tasks
    export/          # Parquet export tasks
config/
  locations.yaml     # Tide locations configuration
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

Example task config (chains ingest → Parquet export):

```yaml
tasks:
  - type: weather_api
    params:
      latitude: 45.123
      longitude: -73.456
      api_key: ${OPENWEATHER_API_KEY}
  - type: weather_parquet
    params:
      output_path: data/weather.parquet
  - type: weather_forecast_api
    params:
      latitude: 45.123
      longitude: -73.456
      api_key: ${OPENWEATHER_API_KEY}
  - type: weather_forecast_parquet
    params:
      output_path: data/weather_forecast.parquet
```

Requires [pyarrow](https://arrow.apache.org/docs/python/) (installed via `uv sync`).
