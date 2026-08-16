# Fishing Brain consumer integration

Fishing Brain consumes this weather app via `WEATHER_APP_BASE_URL`.

Contract: see `fishing_brain_app/WEATHER_APP_INTEGRATION_SPEC.md` in the sibling
repo (product name: Fishing Brain), plus `GET /api/weather/{location_id}` for
current conditions.

Start this service with `src.weather.main:app` on port 8001 (not `src.api.main:app`).

- `WEATHER_DATA_SOURCE=fixture` (default) — deterministic observations, no API key
- `WEATHER_DATA_SOURCE=openweather` — live current weather; set `OPENWEATHER_API_KEY`

## Deployment order

1. Start weather app on port 8001
2. Configure Fishing Brain `WEATHER_APP_BASE_URL=http://localhost:8001`
3. Fishing Brain syncs locations on startup and queries tides and weather on demand
