# Weather API provider plan

Implements the REST API contract defined in the Tight Lines repo:
[tight_lines_app/WEATHER_APP_INTEGRATION_SPEC.md](../../tight_lines_app/WEATHER_APP_INTEGRATION_SPEC.md)

## Endpoints

- `GET /api/locations` — tide location catalogue
- `GET /api/tides/{location_id}?start=&end=` — tide predictions with phase
- `GET /api/weather/{location_id}` — latest current conditions for Tight Lines
- `GET /health` — service health check

## Local development

```bash
uv sync --group dev
uv run alembic upgrade head
rtk uv run uvicorn src.weather.main:app --reload --port 8001
```

Set `TIDE_DATA_SOURCE=fixture` for offline tide data (default).
Set `WEATHER_DATA_SOURCE=fixture` for offline current weather (default), or
`WEATHER_DATA_SOURCE=openweather` with `OPENWEATHER_API_KEY` for live conditions.

## Deployment order

1. Deploy weather app with API endpoints
2. Deploy Tight Lines with `WEATHER_APP_BASE_URL` pointing at this service
