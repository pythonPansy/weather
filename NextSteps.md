# Next steps

The repo now runs in two modes:

1. **Service mode** — FastAPI tide API on port 8001 for [Tight Lines integration](docs/integration/tight_lines_consumer.md).
   Use `src.weather.main:app` (SQLite + Admiralty Discovery ingest) or the YAML-backed `src.api.main:app`.
2. **Task runner mode** — YAML-driven ingestion via `TaskRunner` (`weather_api`, `tide_ingest`, Parquet export tasks).

## Completed

- REST API: `GET /api/locations`, `GET /api/tides/{location_id}`
- Fixture and Admiralty Discovery tide ingest with spring/neap/medium phase classification
- Alembic migrations, pytest coverage for API routes
- Integration with Tight Lines consumer (`WEATHER_APP_BASE_URL`)
- Typed `PipelineContext`, CLI entry point (`python -m src`), Parquet export tasks

## Recommended next steps

In order:

1. **Consolidate API layers** — merge `src/api/` (YAML locations) and `src/weather/` (DB + Admiralty) behind one entry point
2. **CSV export task** — export ingested data from task runner context
3. **Custom exceptions** — structured errors for task failures
4. **Task dependencies** — chain tasks with explicit ordering
5. **mypy typing** — strict checks on public API
6. **Incremental runs** — skip unchanged data on re-run

## Testing

```bash
rtk uv run pytest tests -q
rtk uv run ruff check ./src ./tests
```

Smoke test (service running on 8001):

```bash
curl http://localhost:8001/api/locations
curl "http://localhost:8001/api/tides/plym-uk-001?start=2026-08-11T00:00:00Z&end=2026-08-18T00:00:00Z"
```
