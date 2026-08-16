"""Tests for forecast range and nearest-at-time weather endpoints."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.weather.config import get_settings
from src.weather.db import Base, get_session, reset_db_state
from src.weather.main import create_app
from src.weather.services.ingest_weather import (
    fixture_forecast_for_location,
    fixture_weather_for_location,
    ingest_fixture_weather,
)
from src.weather.services.locations import seed_locations


@pytest.mark.asyncio
async def test_forecast_returns_points_in_range(client: AsyncClient) -> None:
    start = datetime.now(tz=UTC).replace(minute=0, second=0, microsecond=0)
    end = start + timedelta(days=2)
    response = await client.get(
        "/api/weather/plym-uk-001/forecast",
        params={"start": start.isoformat(), "end": end.isoformat()},
    )
    assert response.status_code == 200
    data = response.json()
    assert "forecasts" in data
    assert len(data["forecasts"]) >= 1
    point = data["forecasts"][0]
    assert "forecast_at" in point
    assert "temperature_c" in point
    assert "pressure_hpa" in point
    assert "cloud_cover_pct" in point
    assert "moon_phase" in point
    assert point["swell_height_m"] is None


@pytest.mark.asyncio
async def test_current_weather_includes_richer_fields(client: AsyncClient) -> None:
    response = await client.get("/api/weather/plym-uk-001")
    assert response.status_code == 200
    data = response.json()
    expected = fixture_weather_for_location("plym-uk-001")
    assert data["conditions"] == expected.conditions
    assert data["pressure_hpa"] == expected.pressure_hpa
    assert data["cloud_cover_pct"] == expected.cloud_cover_pct
    assert data["moon_phase"] is not None
    assert data["swell_height_m"] is None


@pytest.mark.asyncio
async def test_weather_at_returns_nearest_within_tolerance(
    client: AsyncClient,
) -> None:
    expected = fixture_weather_for_location("plym-uk-001")
    response = await client.get(
        "/api/weather/plym-uk-001/at",
        params={"at": expected.observed_at.isoformat()},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is True
    assert data["matched_at"] is not None
    assert data["source"] in {"observation", "forecast"}
    assert data["temperature_c"] is not None


@pytest.mark.asyncio
async def test_weather_at_miss_outside_tolerance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("WEATHER_DATA_SOURCE", "fixture")
    monkeypatch.setenv("WEATHER_AT_TOLERANCE_HOURS", "1")
    get_settings.cache_clear()
    reset_db_state()

    engine = create_async_engine(get_settings().database_url, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        await seed_locations(session)
        await ingest_fixture_weather(session)

    app = create_app(start_scheduler=False)

    async def override_session():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    from httpx import ASGITransport
    from httpx import AsyncClient as HttpxClient

    transport = ASGITransport(app=app)
    async with HttpxClient(transport=transport, base_url="http://test") as ac:
        far = datetime.now(tz=UTC) - timedelta(days=30)
        response = await ac.get(
            "/api/weather/plym-uk-001/at",
            params={"at": far.isoformat()},
        )
        assert response.status_code == 200
        assert response.json()["available"] is False

    await engine.dispose()
    get_settings.cache_clear()
    reset_db_state()


@pytest.mark.asyncio
async def test_forecast_unknown_location_404(client: AsyncClient) -> None:
    start = datetime.now(tz=UTC)
    end = start + timedelta(days=1)
    response = await client.get(
        "/api/weather/unknown-id/forecast",
        params={"start": start.isoformat(), "end": end.isoformat()},
    )
    assert response.status_code == 404


def test_fixture_forecast_length() -> None:
    points = fixture_forecast_for_location("plym-uk-001")
    assert len(points) == 40
