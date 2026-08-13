# Weather API provider plan

Implements the REST API contract defined in the Tight Lines repo:
[tight_lines_app/WEATHER_APP_INTEGRATION_SPEC.md](../../tight_lines_app/WEATHER_APP_INTEGRATION_SPEC.md)

## Endpoints

- `GET /api/locations` — tide location catalogue
- `GET /api/tides/{location_id}?start=&end=` — tide predictions with phase
- `GET /health` — service health check

## Local development

```bash
uv sync --group dev
uv run alembic upgrade head
rtk uv run uvicorn src.weather.main:app --reload --port 8001
```

Set `TIDE_DATA_SOURCE=fixture` for offline tide data (default).

## Deployment order

1. Deploy weather app with API endpoints
2. Deploy Tight Lines with `WEATHER_APP_BASE_URL` pointing at this service
