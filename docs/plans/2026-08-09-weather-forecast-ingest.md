---
status: approved
created: 2026-08-09
approval: approved
---

# Plan: Weather forecast ingest (alongside current actuals)

## Goal

Add OpenWeatherMap **forecast** ingestion and Parquet export alongside the existing current-weather (actuals) path, so a pipeline run can collect both a point-in-time observation and a forecast payload for the same coordinates, without changing the meaning of the current `weather` / `weather_parquet` data.

## Background

- Today `WeatherAPITask` calls `GET /data/2.5/weather` — **current conditions only**.
- Forecast is a different OWM endpoint: `GET /data/2.5/forecast` (5 day / 3 hour by default).
- Actuals and forecasts should stay separate in context and on disk so time-series analysis is not confused (observation vs prediction).
- Depends on typed `PipelineContext` (landed / in PR). CLI + env expansion (`docs/plans/2026-08-09-cli-env-and-data-collection.md`) is useful for live collection but not required to implement the tasks.

## Scope

### In scope

- New ingest task, e.g. `weather_forecast_api`, calling OWM `/data/2.5/forecast` with `lat`, `lon`, `appid` (same param shape as current weather: `latitude`, `longitude`, `api_key`)
- Extend `PipelineContext` with forecast fields, e.g. `weather_forecast` and `weather_forecast_call`
- New export task, e.g. `weather_forecast_parquet`, appending one row per run to a **separate** file (default `data/weather_forecast.parquet`) with the same column pattern as weather: `latitude`, `longitude`, `fetched_at`, `response`
- Unit tests with mocked `requests.get`; optional `live_api` test gated on `OPENWEATHER_API_KEY`
- Wire tasks into `config/pipeline.yaml` after the current weather pair (or clearly documented order)
- UK English in owned code/docs; do not rename OWM query params on the wire

### Out of scope

- Replacing or changing `/data/2.5/weather` behaviour
- One Call API 3.0, hourly minutely, or paid-only products (stick to free-tier `/forecast` unless plan is revised)
- Normalising nested forecast list items into a first-class UK schema (store full JSON in `response` for v1, same as current weather)
- Flattening forecast timesteps into one Parquet row per `list[]` entry (v1 = one row per fetch, full payload)
- CLI/cron (covered by the data-collection plan)
- Custom exceptions refactor

## Design

### Task types

| Type | Role |
| ---- | ---- |
| `weather_api` (existing) | Current actuals → `context.weather` |
| `weather_parquet` (existing) | Append actuals → `data/weather.parquet` |
| `weather_forecast_api` (new) | Forecast → `context.weather_forecast` |
| `weather_forecast_parquet` (new) | Append forecast → `data/weather_forecast.parquet` |

### Context

```python
# additions on PipelineContext
weather_forecast: dict | None = None
weather_forecast_call: dict | None = None
weather_forecast_parquet_path: str | None = None
```

### Suggested YAML fragment

```yaml
  - type: weather_forecast_api
    params:
      latitude: 45.123
      longitude: -73.456
      api_key: ${OPENWEATHER_API_KEY}
  - type: weather_forecast_parquet
    params:
      output_path: data/weather_forecast.parquet
```

### API notes

- URL: `https://api.openweathermap.org/data/2.5/forecast`
- Query: `lat`, `lon`, `appid` (optional later: `units`, `cnt`)
- Response includes `list` of 3-hourly forecast entries; v1 stores the whole JSON blob like current weather

## Files to touch

| File | Change |
| ---- | ------ |
| `src/context.py` | Add forecast fields |
| `src/tasks/ingest/weather_forecast_api.py` | New task + `@register_task` |
| `src/tasks/ingest/__init__.py` | Import new module for registration |
| `src/tasks/export/weather_forecast_parquet.py` | New export task |
| `src/tasks/export/__init__.py` | Import new module for registration |
| `tests/tasks/test_weather_forecast_task.py` | Mocked ingest tests |
| `tests/tasks/test_weather_forecast_parquet_task.py` | Export / missing-context tests |
| `tests/tasks/test_weather_forecast_task_live.py` | Optional live marker |
| `tests/context/test_pipeline_context.py` | Defaults for new fields |
| `config/pipeline.yaml` | Add forecast ingest + export |
| `README.md` | Note actuals vs forecast endpoints and output files |

## Implementation steps

1. Extend `PipelineContext` (+ unit test defaults).
2. TDD ingest: mock OWM forecast payload; assert `weather_forecast` / `weather_forecast_call` set; assert URL/params.
3. Implement `WeatherForecastAPITask`.
4. TDD export: write/append Parquet; `require` failures when forecast missing.
5. Implement `WeatherForecastParquetTask` (mirror weather parquet helpers or share a small private append helper only if duplication is painful — prefer copy-paste twin over premature abstraction).
6. Register via package imports; update `config/pipeline.yaml` and README.
7. Validate with ruff + non-live pytest.

## Validation

```bash
rtk uv run ruff check ./src ./tests
rtk uv run ruff format --check .
rtk uv run pytest tests/context tests/tasks/test_weather_forecast_task.py tests/tasks/test_weather_forecast_parquet_task.py -q
rtk uv run pytest -q
```

Live (opt-in, needs approval + key):

```bash
rtk uv run pytest tests/tasks/test_weather_forecast_task_live.py -m live_api -q
```

## Risks

- OWM free-tier rate limits: one run hits weather + forecast (+ tides); document if cron is frequent.
- Storing full forecast JSON per run grows Parquet faster than current weather; acceptable for v1; note for later timestep-normalisation.
- Env expansion must exist (or key inlined via env-only test params) before live YAML runs work with `${OPENWEATHER_API_KEY}`.

## Approval

- [ ] **waiting** — stored for later; user has not approved implementation
- [x] **approved** — date: 2026-08-09 (user: implement outstanding plans)
