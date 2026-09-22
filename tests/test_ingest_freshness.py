"""Tests for skip-if-fresh tide and weather ingest."""

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.weather.config import get_settings
from src.weather.db import Base, reset_db_state
from src.weather.models import WeatherForecast
from src.weather.services.ingest import ingest_fixture_tides, run_tide_ingest
from src.weather.services.ingest_weather import (
    ingest_fixture_weather,
    run_weather_ingest,
    weather_store_is_fresh,
)
from src.weather.services.locations import seed_locations


@pytest.fixture
async def session_factory(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("TIDE_DATA_SOURCE", "fixture")
    monkeypatch.setenv("WEATHER_DATA_SOURCE", "fixture")
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
async def test_run_tide_ingest_skips_when_fresh(session_factory, monkeypatch) -> None:
    monkeypatch.setattr(
        "src.weather.services.ingest.get_session_factory",
        lambda: session_factory,
    )

    async with session_factory() as session:
        first = await ingest_fixture_tides(session)
    assert first > 0

    second = await run_tide_ingest()
    assert second == 0


@pytest.mark.asyncio
async def test_run_weather_ingest_skips_when_fresh(
    session_factory, monkeypatch
) -> None:
    monkeypatch.setattr(
        "src.weather.services.ingest_weather.get_session_factory",
        lambda: session_factory,
    )

    async with session_factory() as session:
        first = await ingest_fixture_weather(session)
    assert first > 0

    second = await run_weather_ingest()
    assert second == 0


@pytest.mark.asyncio
async def test_weather_store_not_fresh_without_forecasts(
    session_factory, monkeypatch
) -> None:
    monkeypatch.setattr(
        "src.weather.services.ingest_weather.get_session_factory",
        lambda: session_factory,
    )

    async with session_factory() as session:
        await ingest_fixture_weather(session)
        await session.execute(delete(WeatherForecast))
        await session.commit()
        assert await weather_store_is_fresh(session) is False

    count = await run_weather_ingest(force=True)
    assert count > 0
