---
status: partial
created: 2026-08-13
approval: waiting
branch: feature/weather-admiralty-api
pr: https://github.com/pythonPansy/weather/pull/6
---

# Weather API provider plan

## Implementation status

**Partial** — primary implementation on `feature/weather-admiralty-api` ([PR #6](https://github.com/pythonPansy/weather/pull/6)), not yet merged to `main`.

| Item | `main` (`src/api/`) | Feature branch (`src/weather/`) |
| ---- | ------------------- | -------------------------------- |
| `GET /api/locations` | Done (YAML) | Done (SQLite) |
| `GET /api/tides/{location_id}` | Done | Done |
| `GET /health` | Missing | Done |
| Admiralty Discovery ingest | — | Done |
| Alembic + `.env.example` | — | Done |
| Tests | `tests/api/` | `tests/test_*_api.py`, Admiralty tests |

**Remaining before close:**

- Merge PR #6 to `main`
- Consolidate `src/api/` and `src/weather/` behind one entry point (`NextSteps.md`)
- Add `/health` test; align `.env.example` default with fixture-first offline dev
- Add `/health` to YAML-backed `src/api/` if that entry point is kept

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
3. Verify endpoints before enabling notifications

## Approval

- [x] **waiting** — merge PR #6 and close remaining items above
- [ ] **approved** — date: YYYY-MM-DD
- [ ] **completed** — date: YYYY-MM-DD
