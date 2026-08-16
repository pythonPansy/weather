import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.weather.config import get_settings
from src.weather.db import Base, reset_db_state
from src.weather.services.ingest_weather import fixture_weather_for_location
from src.weather.services.locations import seed_locations
from src.weather.services.weather import get_weather_for_location


@pytest.mark.asyncio
async def test_weather_returns_fixture_shape(client: AsyncClient) -> None:
    response = await client.get("/api/weather/plym-uk-001")
    assert response.status_code == 200
    data = response.json()
    expected = fixture_weather_for_location("plym-uk-001")
    assert data["conditions"] == expected.conditions
    assert data["wind_direction"] == expected.wind_direction
    assert data["temperature_c"] == expected.temperature_c
    assert data["wind_speed_mph"] == expected.wind_speed_mph
    assert data["summary"] == expected.summary
    assert data["observed_at"] is not None


@pytest.mark.asyncio
async def test_weather_unknown_location_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/weather/unknown-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_weather_missing_observation_returns_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("WEATHER_DATA_SOURCE", "fixture")
    get_settings.cache_clear()
    reset_db_state()

    engine = create_async_engine(get_settings().database_url, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        await seed_locations(session)
        with pytest.raises(HTTPException) as exc_info:
            await get_weather_for_location(session, "plym-uk-001")
        assert exc_info.value.status_code == 503

    await engine.dispose()
    get_settings.cache_clear()
    reset_db_state()
