# Tight Lines consumer integration

Tight Lines consumes this weather app via `WEATHER_APP_BASE_URL`.

Contract: see `tight_lines_app/WEATHER_APP_INTEGRATION_SPEC.md` in the sibling repo.

## Deployment order

1. Start weather app on port 8001
2. Configure Tight Lines `WEATHER_APP_BASE_URL=http://localhost:8001`
3. Tight Lines syncs locations on startup and queries tides on demand
