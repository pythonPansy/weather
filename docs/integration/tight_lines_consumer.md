# Fishing Brain consumer integration

Fishing Brain consumes this weather app via `WEATHER_APP_BASE_URL`.

Start this service with `src.weather.main:app` on port 8001 (not `src.api.main:app`).

Contract details: see `fishing_brain_app/WEATHER_APP_INTEGRATION_SPEC.md` in the
sibling repo.

## Endpoints

| Method | Path | Purpose |
| ------ | ---- | ------- |
| `GET` | `/api/locations` | Tide station catalogue |
| `GET` | `/api/tides/{location_id}?start=&end=` | Tide predictions (ISO 8601 range) |
| `GET` | `/api/weather/{location_id}` | Current conditions |
| `GET` | `/api/weather/{location_id}/at?at=` | Nearest observation or forecast to a timestamp |
| `GET` | `/api/weather/{location_id}/forecast?start=&end=` | Forecast points in a date range |
| `GET` | `/health` | Liveness |

### Weather fields (current, at-time, and forecast points)

All weather payloads share these nullable fields where data exists:

- `summary`, `conditions`, `wind_speed_mph`, `wind_direction`, `temperature_c`
- `pressure_hpa`, `cloud_cover_pct`, `humidity_pct`, `moon_phase`
- `swell_height_m`, `swell_period_s`, `swell_direction`

`/at` responses also include:

- `available` (boolean)
- `matched_at`, `delta_seconds`, `source` (`observation` | `forecast`)

Forecast points include `forecast_at` instead of `observed_at`.

## Configuration

- `WEATHER_DATA_SOURCE=fixture` (default) — deterministic observations, no API key
- `WEATHER_DATA_SOURCE=openweather` — live current weather; set `OPENWEATHER_API_KEY`
- `WEATHER_AT_TOLERANCE_HOURS` — matching window for `/at` (default 3)

## Deployment order

1. Deploy weather app first.
2. Configure Fishing Brain `WEATHER_APP_BASE_URL` to the weather service URL.
3. Verify `GET /api/locations`, tides, current weather, `/at`, and `/forecast`.
4. Deploy Fishing Brain and test catch enrichment, planner, and notifications.
