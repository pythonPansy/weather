from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.weather.config import get_settings
from src.weather.db import Base, reset_db_state
from src.weather.models import WeatherObservation
from src.weather.services.ingest_weather import ingest_openweather
from src.weather.services.locations import seed_locations
from src.weather.services.openweather_client import (
    CurrentWeather,
    OpenWeatherApiError,
)


@pytest.fixture
async def session_factory(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("WEATHER_DATA_SOURCE", "openweather")
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-key")
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
async def test_ingest_openweather_skips_failures(session_factory) -> None:
    weather = CurrentWeather(
        summary="Clear sky, 12.0°C, SW 8.0 mph",
        wind_speed_mph=8.0,
        wind_direction="SW",
        temperature_c=12.0,
        conditions="Clear sky",
        observed_at=datetime(2026, 8, 14, 7, 0, tzinfo=UTC),
    )

    mock_client = AsyncMock()
    mock_client.get_current_weather = AsyncMock(
        side_effect=[weather, OpenWeatherApiError("boom")] + [weather] * 20
    )
    mock_client.close = AsyncMock()

    with patch(
        "src.weather.services.ingest_weather.OpenWeatherClient",
        return_value=mock_client,
    ):
        async with session_factory() as session:
            count = await ingest_openweather(session)
            stored = await session.get(WeatherObservation, "plym-uk-001")

    assert count >= 1
    assert stored is not None
    assert stored.wind_direction == "SW"
    mock_client.close.assert_awaited()
