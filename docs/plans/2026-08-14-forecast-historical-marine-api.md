---
status: approved
created: 2026-08-14
approval: approved
approved_date: 2026-08-14
approved_slices: W1, W2, W3
---

# Plan: Forecast, historical-at-time, and richer marine weather API

## Goal

Extend the Tight Lines-facing weather service (`src.weather.main:app`) so angler clients can (1) load a multi-day weather forecast for a station, (2) resolve conditions nearest to a catch timestamp, and (3) expose richer marine-relevant fields (pressure, cloud cover, optional swell/moon) under a stable UK-English JSON contract. This unblocks Tight Lines phases B, D, and E in `fishing_brain_app/docs/plans/2026-08-14-competitive-parity-conditions-insights.md`.

## Background

Today:

- `GET /api/weather/{location_id}` returns the **latest** observation only (`WeatherRead`: summary, wind, temperature, conditions, `observed_at`)
- Tide range already supports `?start=&end=` with height + phase
- YAML pipeline has `weather_forecast_api` → Parquet, but **no REST forecast** for Tight Lines
- Current-weather plan explicitly out-of-scoped forecast range and marine extras

Tight Lines notification engine and catch enrichment must not call OpenWeatherMap directly — only this API.

## Scope

### In scope

#### W1 — Forecast range API

- Persist forecast timesteps per location (from OpenWeather `/data/2.5/forecast` or equivalent free-tier source; fixture mode for tests)
- `GET /api/weather/{location_id}?start=&end=` **or** dedicated `GET /api/weather/{location_id}/forecast?start=&end=`
  - Prefer a **dedicated forecast path** so “current” behaviour stays unchanged for existing clients
- Response: list of points with UK keys (`forecast_at`, `temperature_c`, `wind_speed_mph`, `wind_direction`, `conditions`, `pressure_hpa`, `cloud_cover_pct`, …)
- Horizon: at least ~5 days (OWM free forecast); document as “up to N days”
- Ingest on schedule alongside current weather; fixture data deterministic

#### W2 — Conditions at a point in time (historical / nearest)

Support catch enrichment: “what was it like at this place and `caught_at`?”

**Preferred v1 (no paid historical API):**

- Keep a rolling store of observations (and/or forecast timesteps) with timestamps
- `GET /api/weather/{location_id}/at?at={iso8601}` returns the nearest stored point within a configurable tolerance (e.g. ±3 hours), or 404/`available: false` style empty payload
- Optionally accept lat/lon later; v1 uses station id only (Tight Lines resolves nearest station)

**v2 (optional, gated):**

- Paid OpenWeather One Call / timemachine or Open-Meteo archive — only if rolling store is too sparse for retrospective catches older than retention

#### W3 — Richer fields on current + forecast + at-time

Extend owned schema (nullable when unknown):

| Field | Notes |
| ----- | ----- |
| `pressure_hpa` | From OWM `main.pressure` |
| `cloud_cover_pct` | From OWM `clouds.all` |
| `humidity_pct` | Optional; useful for display |
| `moon_phase` | Compute astronomically from datetime (no vendor required) or provider |
| `swell_height_m` / `swell_period_s` / `swell_direction` | Only if a marine source is added; otherwise omit or always null in v1 |

Keep existing keys stable. Add fields; do not rename.

#### W4 — Tide helpers for “bigger springs / small neaps”

Tight Lines mark rules need more than `phase: spring|neap`:

- Ensure predictions expose `height` reliably (already on `TidePredictionRead`)
- Document how clients can compare upcoming lows/highs to location MHWS/MHWN (already on locations) to classify “larger spring” vs “smaller neap”
- Optional convenience on tide list or location: `tidal_coefficient` or `range_m` for the day — only if cheap to compute from stored highs/lows

No fishing-species logic in this repo.

### Out of scope

- User accounts, notifications, insights, EXIF (Tight Lines)
- Changing Parquet YAML pipeline contracts (may reuse mapping helpers)
- Guaranteeing swell for every UK mark on day one
- CORS/auth beyond what already exists
- Worldwide coverage beyond seeded UK locations

## Contract sketches (Tight Lines-facing)

### Forecast

```http
GET /api/weather/{location_id}/forecast?start=2026-08-14T00:00:00Z&end=2026-08-21T00:00:00Z
```

```json
{
  "forecasts": [
    {
      "forecast_at": "2026-08-14T12:00:00Z",
      "temperature_c": 14.2,
      "wind_speed_mph": 12.0,
      "wind_direction": "SW",
      "conditions": "Light rain",
      "pressure_hpa": 1012.0,
      "cloud_cover_pct": 80,
      "summary": "Light rain, 14.2°C, SW 12 mph"
    }
  ]
}
```

### At time

```http
GET /api/weather/{location_id}/at?at=2026-08-10T18:30:00Z
```

Same shape as enriched `WeatherRead` (+ richer fields), plus `matched_at` and maybe `delta_seconds`.

### Current (backward compatible)

Existing `GET /api/weather/{location_id}` gains optional richer fields; old clients ignore unknowns.

## Files to touch

| File | Change |
| ---- | ------ |
| `src/weather/models.py` | Forecast timestep table; possibly multi-row observations history |
| `alembic/versions/…` | Migrations |
| `src/weather/schemas.py` | Forecast list, at-time, extended weather fields |
| `src/weather/routes/api.py` | New routes |
| `src/weather/services/weather.py` | Query nearest / range |
| `src/weather/services/openweather_client.py` | Forecast fetch + richer mapping |
| `src/weather/services/ingest.py` | Persist forecast + retain observation history |
| `src/weather/config.py` | Retention hours, tolerance, marine source flags |
| `tests/` | Fixture ingest + API tests |
| Docs / `.env.example` | Contract notes for Tight Lines |

Optional later: marine client module if swell provider chosen.

## Implementation steps

1. Extend observation mapping with pressure / cloud (and humidity); migrate columns; keep current endpoint working.
2. Add forecast ingest + table + `/forecast` range endpoint (fixture + openweather).
3. Retain observation history (or reuse forecast/obs timesteps) + `/at` nearest-neighbour endpoint.
4. Add moon phase helper from `caught_at` / `forecast_at` (pure function).
5. Document MHWS/MHWN comparison for spring/neap magnitude; optional `range_m` on daily tide summary if easy.
6. Decide swell: stub null fields **or** add one marine provider behind a feature flag.
7. Coordinate Tight Lines client updates (`WeatherAppClient`) in the companion TL phases — not in this repo unless a dual-repo PR is requested.

## Validation

```bash
rtk uv run ruff check ./src ./tests
rtk uv run ruff format --check .
rtk uv run pytest tests/ -q
```

Manual:

- Fixture mode: forecast returns multiple points for a seeded id
- `/at` within tolerance returns a point; far outside → clear miss
- Current endpoint still matches Tight Lines’ existing fields
- No live OWM calls in default unit tests

## Risks

- Free OWM forecast is 3-hourly and ~5 days — trip planner “7-day” may be “5-day + tides for 7”
- Retention vs disk: bound history (e.g. 30–90 days) for `/at`
- Paid historical APIs — avoid until retention proven insufficient
- Swell providers add cost and another failure mode — keep nullable
- Dual apps (`src.api` vs `src.weather`) — only extend `src.weather` for Tight Lines

## Approval

- [ ] **waiting** — user has not approved
- [x] **approved** — date: 2026-08-14
- [x] **approved slices** — W1, W2, W3 (swell nullable stub; W4 optional later)
