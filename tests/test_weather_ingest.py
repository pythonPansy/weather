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
        pressure_hpa=1013.0,
        cloud_cover_pct=10,
        humidity_pct=72,
        moon_phase="Waxing crescent",
        swell_height_m=None,
        swell_period_s=None,
        swell_direction=None,
        observed_at=datetime(2026, 8, 14, 7, 0, tzinfo=UTC),
    )

    async def _current_side_effect(*_args, **_kwargs):
        call = mock_client.get_current_weather.await_count
        if call == 2:
            raise OpenWeatherApiError("boom")
        return weather

    mock_client = AsyncMock()
    mock_client.get_current_weather = AsyncMock(side_effect=_current_side_effect)
    mock_client.get_forecast = AsyncMock(return_value=[weather])
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
