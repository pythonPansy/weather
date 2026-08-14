---
status: approved
created: 2026-08-14
approval: approved
---

# Plan: Current weather API for Tight Lines

## Goal

Add `GET /api/weather/{location_id}` to the Tight Lines-facing weather app (`src.weather.main:app`) so the frontend catch form, JSON proxy, and Expo client can load current conditions (summary, wind, temperature, observed time) instead of showing “unavailable until the weather app endpoint is live.”

Tight Lines already calls this contract via `WeatherAppClient.get_weather` in `tight_lines_app/src/tight_lines/services/weather_client.py`. Locations and tides endpoints already exist; weather is the missing piece.

## Background

Tight Lines (web + mobile) now loads station conditions with:

```
GET /api/weather/{location_id}
```

Expected JSON (UK English keys; matches `WeatherRead` / the client docstring):

```json
{
  "summary": "Clear sky, 12.0°C, SW 8 mph",
  "wind_speed_mph": 8.0,
  "wind_direction": "SW",
  "temperature_c": 12.0,
  "conditions": "Clear sky",
  "observed_at": "2026-08-14T07:00:00+00:00"
}
```

Unknown location → HTTP 404. Tight Lines treats other HTTP errors as `available: false` and does not crash.

The weather service already:

- Seeds UK locations and serves `GET /api/locations` and `GET /api/tides/{location_id}`
- Ingests tides on startup + daily scheduler (`fixture` or Admiralty)
- Collects OpenWeatherMap current/forecast JSON into Parquet via the YAML pipeline (`WeatherAPITask`) — that path is **not** what Tight Lines reads

Follow the tide pattern: store a latest observation per location, ingest on startup (and on a short schedule), serve from Postgres/SQLite.

## Scope

### In scope

- `GET /api/weather/{location_id}` on `src.weather.main:app` matching the Tight Lines contract above
- Map OpenWeatherMap current-weather payloads into the owned UK schema (`temperature_c`, `wind_speed_mph`, compass `wind_direction`, `conditions`, `summary`, `observed_at`)
- Persist **one latest observation per location** (upsert)
- Dual data source, same idea as tides:
  - `WEATHER_DATA_SOURCE=fixture` (default) — deterministic observations so local Tight Lines and unit tests work without a live key
  - `WEATHER_DATA_SOURCE=openweather` — fetch `/data/2.5/weather` per seeded location using `OPENWEATHER_API_KEY`
- Ingest on app startup and hourly via the existing APScheduler in `src/weather/main.py`
- Alembic migration, settings, `.env.example`, README / integration docs
- Unit tests with mocked HTTP; optional `live_api` test gated on `OPENWEATHER_API_KEY`

### Out of scope

- Forecast range API (`GET /api/weather/{id}?start=&end=`) — Tight Lines marked this as a future enhancement; current UI only needs latest conditions
- Changing the YAML pipeline / Parquet exporters (`weather_api`, `weather_forecast_api`)
- Extending the older YAML-backed app `src.api.main:app` (Tight Lines uses `src.weather.main:app` on port 8001)
- CORS, authentication, or rate limiting
- Sea-state / pressure / humidity fields (not in the Tight Lines contract)
- Tight Lines code changes (client already implements the contract)

## Files to touch

| File | Change |
| ---- | ------ |
| `src/weather/models.py` | Add `WeatherObservation` (FK to `locations.id`, unique per location) |
| `alembic/versions/0003_weather_observations.py` | Create `weather_observations` table |
| `src/weather/schemas.py` | Add `WeatherRead` matching Tight Lines fields |
| `src/weather/routes/api.py` | `GET /api/weather/{location_id}` |
| `src/weather/services/weather.py` | Load latest observation; 404 if location missing; 503 if none stored |
| `src/weather/services/openweather_client.py` | Async httpx client + mapping helpers (m/s → mph, degrees → compass) |
| `src/weather/services/ingest.py` (or `ingest_weather.py`) | Fixture ingest + OpenWeather ingest; `run_weather_ingest()` |
| `src/weather/config.py` | `weather_data_source`, `openweather_api_key` |
| `src/weather/main.py` | Startup weather ingest + hourly job |
| `tests/conftest.py` | Seed fixture weather alongside fixture tides |
| `tests/test_weather_api.py` | Endpoint shape, 404, 503-if-empty (if exercised) |
| `tests/test_openweather_client.py` | Mapping unit tests (mocked payload, no network) |
| `.env.example` | Document `WEATHER_DATA_SOURCE` and `OPENWEATHER_API_KEY` |
| `README.md` | List the new endpoint; keep Tight Lines on `src.weather.main:app` |
| `docs/integration/tight_lines_consumer.md` | Note weather endpoint and fixture vs live |
| `docs/plans/weather-api-provider.md` | Add the weather endpoint to the contract list |

## Implementation steps

1. **Model + migration** — `weather_observations`: `location_id` PK/unique FK, `summary`, `wind_speed_mph`, `wind_direction`, `temperature_c`, `conditions`, `observed_at` (timezone-aware). App already runs `create_all` on startup; still add Alembic `0003` for real databases.

2. **Mapping (pure functions, easy to test)** — OpenWeatherMap current weather (`units=metric`):
   - `main.temp` → `temperature_c` (already Celsius with `units=metric`)
   - `wind.speed` is **metres per second** even with metric units → `wind_speed_mph = round(mps * 2.2369362920544, 1)`
   - `wind.deg` → 8-point compass (`N`, `NE`, `E`, `SE`, `S`, `SW`, `W`, `NW`); missing deg → `null`
   - `weather[0].description` → `conditions` (title-case the description)
   - `dt` (unix UTC) → `observed_at`
   - `summary` = `"{conditions}, {temperature_c}°C, {wind_direction} {wind_speed_mph} mph"` omitting missing parts
   - Do not rename OWM query params on the wire (`lat`, `lon`, `appid`, `units`)

3. **Ingest**
   - Fixture: one observation per seeded location; deterministic values derived from location id so tests can assert Plymouth (`plym-uk-001`) without snapshots of all stations
   - Live: for each location, `GET https://api.openweathermap.org/data/2.5/weather`; upsert observation; log and skip a station on HTTP failure rather than aborting the whole run
   - `require_openweather_api_key()` when source is `openweather`, mirroring Admiralty

4. **API route** — same style as tides: look up location, then latest observation. 404 location not found; 503 if the location exists but has no observation yet (Tight Lines already treats this as unavailable).

5. **Scheduler** — after tide ingest on startup, run weather ingest. Add hourly cron (e.g. minute 0) next to the existing 02:00 tide job. Default `WEATHER_DATA_SOURCE=fixture` so `uv run pytest` and local Tight Lines work without a key.

6. **Tests** — extend `client` fixture to ingest fixture weather. Cover 200 shape for `plym-uk-001`, 404 unknown id, compass/mph mapping from a canned OWM JSON. Do not call live OWM in the default suite.

7. **Docs** — README service-mode endpoint list; integration doc deployment order unchanged (weather app first, then Tight Lines).

## Validation

```bash
rtk uv run ruff check ./src ./tests
rtk uv run ruff format --check .
rtk uv run pytest tests/test_weather_api.py tests/test_openweather_client.py tests/test_locations_api.py tests/test_tides_api.py -q
```

Manual (after implement, local only; live OWM needs your approval):

```bash
# fixture mode — no OpenWeather key
TIDE_DATA_SOURCE=fixture WEATHER_DATA_SOURCE=fixture \
  rtk uv run uvicorn src.weather.main:app --reload --port 8001

curl -s http://localhost:8001/api/weather/plym-uk-001 | jq
```

Tight Lines (`WEATHER_APP_BASE_URL=http://localhost:8001`) should then show a weather line on the catch form instead of the unavailable message.

## Risks

- **Two FastAPI apps** — README still mentions `src.api.main:app`. If someone starts that process, the new endpoint will be missing. Docs will state clearly that Tight Lines must use `src.weather.main:app`.
- **OWM units** — wind stays m/s unless we convert; forgetting the conversion would show ~2× too-low mph values.
- **Hourly ingest vs on-demand** — cached observations can be up to ~1 hour stale. Acceptable for the catch-form “current conditions” display; on-demand live fetch can be a follow-up if freshness matters.
- **Live key in `.env`** — never commit; fixture remains the test default.
- **`create_all` vs Alembic** — existing app creates tables on startup; migration still needed for anyone using `alembic upgrade head` against a file SQLite/Postgres database.

## Approval

- [x] **waiting** — user has not approved
- [x] **approved** — date: 2026-08-14
