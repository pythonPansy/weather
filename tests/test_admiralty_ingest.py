"""Tests for Admiralty tide ingestion."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.weather.config import get_settings
from src.weather.db import Base, reset_db_state
from src.weather.models import Location, TidePrediction
from src.weather.services.admiralty_client import AdmiraltyTidalEvent
from src.weather.services.ingest import ingest_admiralty_tides
from src.weather.services.locations import seed_locations


@pytest.fixture
async def session_factory(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("TIDE_DATA_SOURCE", "admiralty_discovery")
    monkeypatch.setenv("ADMIRALTY_API_KEY", "test-subscription-key")
    monkeypatch.setenv("TIDE_FORECAST_DAYS", "7")
    get_settings.cache_clear()
    reset_db_state()

    engine = create_async_engine(get_settings().database_url, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        await seed_locations(session)

    yield factory

    await engine.dispose()
    get_settings.cache_clear()
    reset_db_state()


@pytest.mark.asyncio
async def test_ingest_admiralty_stores_events(session_factory) -> None:
    events = [
        AdmiraltyTidalEvent(
            event_time=datetime(2026, 8, 13, 7, 54, tzinfo=UTC),
            event_type="high",
            height_metres=4.44,
        ),
        AdmiraltyTidalEvent(
            event_time=datetime(2026, 8, 13, 13, 41, tzinfo=UTC),
            event_type="low",
            height_metres=0.56,
        ),
    ]

    mock_client = AsyncMock()

    async def resolve(name: str) -> str | None:
        return "0123" if name == "Minehead" else None

    mock_client.resolve_station_id = AsyncMock(side_effect=resolve)
    mock_client.get_tidal_events = AsyncMock(return_value=events)
    mock_client.close = AsyncMock()

    with patch(
        "src.weather.services.ingest.AdmiraltyClient",
        return_value=mock_client,
    ):
        async with session_factory() as session:
            count = await ingest_admiralty_tides(session)
            location = await session.get(Location, "mine-uk-003")
            result = await session.execute(
                select(TidePrediction).where(
                    TidePrediction.location_id == "mine-uk-003"
                )
            )
            rows = result.scalars().all()

    assert count == 2
    assert location is not None
    assert location.admiralty_station_id == "0123"
    assert len(rows) == 2


@pytest.mark.asyncio
async def test_ingest_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIRALTY_API_KEY", "")
    get_settings.cache_clear()

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        with pytest.raises(ValueError, match="ADMIRALTY_API_KEY"):
            await ingest_admiralty_tides(session)

    await engine.dispose()
    get_settings.cache_clear()
    reset_db_state()
