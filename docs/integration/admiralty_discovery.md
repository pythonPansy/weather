# Admiralty Discovery tide ingest

## Signup (required — free)

1. Open [Admiralty API Developer Portal](https://developer.admiralty.co.uk/product#product=uk-tidal-api)
2. Create an account and subscribe to **UK Tidal API – Discovery** (free 1-year subscription)
3. Go to **Profile** → show **Primary key**
4. Copy the key into `.env` — never commit it

```env
TIDE_DATA_SOURCE=admiralty_discovery
ADMIRALTY_API_KEY=your-primary-subscription-key
TIDE_FORECAST_DAYS=7
```

Discovery provides **today plus 6 days** (7-day window). Quota: 10,000 calls/month.

## Local run

```bash
cp .env.example .env
# Edit .env and paste ADMIRALTY_API_KEY
uv run alembic upgrade head
uv run uvicorn src.weather.main:app --reload --port 8001
```

## Station mapping

Locations include `admiralty_station_name` for UKHO lookup (e.g. Minehead, Teignmouth (Approaches)).
On first ingest, the app resolves and caches `admiralty_station_id`.

## Offline / CI

Set `TIDE_DATA_SOURCE=fixture` and leave `ADMIRALTY_API_KEY` empty.
