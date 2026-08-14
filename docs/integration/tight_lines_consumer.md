# Tight Lines consumer integration

Tight Lines consumes this weather app via `WEATHER_APP_BASE_URL`.

Contract: see `tight_lines_app/WEATHER_APP_INTEGRATION_SPEC.md` in the sibling
repo, plus `GET /api/weather/{location_id}` for current conditions.

Start this service with `src.weather.main:app` on port 8001 (not `src.api.main:app`).

- `WEATHER_DATA_SOURCE=fixture` (default) — deterministic observations, no API key
- `WEATHER_DATA_SOURCE=openweather` — live current weather; set `OPENWEATHER_API_KEY`

## Deployment order

1. Start weather app on port 8001
2. Configure Tight Lines `WEATHER_APP_BASE_URL=http://localhost:8001`
3. Tight Lines syncs locations on startup and queries tides and weather on demand
