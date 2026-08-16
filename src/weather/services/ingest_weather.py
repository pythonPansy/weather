"""Current-weather and forecast ingestion — fixture mode and OpenWeatherMap."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.weather.config import get_settings
from src.weather.db import get_session_factory
from src.weather.models import (
    Location,
    WeatherForecast,
    WeatherObservation,
    WeatherObservationHistory,
)
from src.weather.services.moon import moon_phase_name
from src.weather.services.openweather_client import (
    OpenWeatherApiError,
    OpenWeatherClient,
    WeatherPoint,
    build_summary,
)

logger = logging.getLogger(__name__)

_COMPASS_8 = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


def fixture_weather_for_location(
    location_id: str, *, observed_at: datetime | None = None
) -> WeatherPoint:
    """Deterministic observation derived from the location id."""
    seed = sum(ord(character) for character in location_id)
    temperature_c = round(10.0 + (seed % 8), 1)
    wind_speed_mph = round(6.0 + (seed % 10), 1)
    wind_direction = _COMPASS_8[seed % 8]
    conditions = "Partly cloudy"
    pressure_hpa = round(1008.0 + (seed % 20), 1)
    cloud_cover_pct = 20 + (seed % 60)
    humidity_pct = 55 + (seed % 30)
    stamp = observed_at or datetime.now(tz=UTC).replace(second=0, microsecond=0)
    return WeatherPoint(
        summary=build_summary(
            conditions=conditions,
            temperature_c=temperature_c,
            wind_direction=wind_direction,
            wind_speed_mph=wind_speed_mph,
        ),
        wind_speed_mph=wind_speed_mph,
        wind_direction=wind_direction,
        temperature_c=temperature_c,
        conditions=conditions,
        pressure_hpa=pressure_hpa,
        cloud_cover_pct=cloud_cover_pct,
        humidity_pct=humidity_pct,
        moon_phase=moon_phase_name(stamp),
        swell_height_m=None,
        swell_period_s=None,
        swell_direction=None,
        observed_at=stamp,
    )


def fixture_forecast_for_location(location_id: str) -> list[WeatherPoint]:
    """Deterministic 3-hourly forecast points for ~5 days (40 steps)."""
    base = datetime.now(tz=UTC).replace(minute=0, second=0, microsecond=0)
    points: list[WeatherPoint] = []
    seed = sum(ord(character) for character in location_id)
    for step in range(40):
        stamp = base + timedelta(hours=3 * step)
        temperature_c = round(9.0 + (seed % 8) + (step % 5) * 0.4, 1)
        wind_speed_mph = round(5.0 + ((seed + step) % 12), 1)
        wind_direction = _COMPASS_8[(seed + step) % 8]
        conditions = "Partly cloudy" if step % 3 else "Light rain"
        pressure_hpa = round(1005.0 + ((seed + step) % 25), 1)
        cloud_cover_pct = min(100, 15 + ((seed + step * 7) % 80))
        humidity_pct = min(100, 50 + ((seed + step) % 40))
        points.append(
            WeatherPoint(
                summary=build_summary(
                    conditions=conditions,
                    temperature_c=temperature_c,
                    wind_direction=wind_direction,
                    wind_speed_mph=wind_speed_mph,
                ),
                wind_speed_mph=wind_speed_mph,
                wind_direction=wind_direction,
                temperature_c=temperature_c,
                conditions=conditions,
                pressure_hpa=pressure_hpa,
                cloud_cover_pct=cloud_cover_pct,
                humidity_pct=humidity_pct,
                moon_phase=moon_phase_name(stamp),
                swell_height_m=None,
                swell_period_s=None,
                swell_direction=None,
                observed_at=stamp,
            )
        )
    return points


def _to_decimal(value: float | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _apply_fields(target: object, weather: WeatherPoint) -> None:
    target.summary = weather.summary  # type: ignore[attr-defined]
    target.wind_speed_mph = _to_decimal(weather.wind_speed_mph)  # type: ignore[attr-defined]
    target.wind_direction = weather.wind_direction  # type: ignore[attr-defined]
    target.temperature_c = _to_decimal(weather.temperature_c)  # type: ignore[attr-defined]
    target.conditions = weather.conditions  # type: ignore[attr-defined]
    target.pressure_hpa = _to_decimal(weather.pressure_hpa)  # type: ignore[attr-defined]
    target.cloud_cover_pct = weather.cloud_cover_pct  # type: ignore[attr-defined]
    target.humidity_pct = weather.humidity_pct  # type: ignore[attr-defined]
    target.moon_phase = weather.moon_phase  # type: ignore[attr-defined]
    target.swell_height_m = _to_decimal(weather.swell_height_m)  # type: ignore[attr-defined]
    target.swell_period_s = _to_decimal(weather.swell_period_s)  # type: ignore[attr-defined]
    target.swell_direction = weather.swell_direction  # type: ignore[attr-defined]


async def _upsert_observation(
    session: AsyncSession, location_id: str, weather: WeatherPoint
) -> None:
    existing = await session.get(WeatherObservation, location_id)
    if existing is None:
        row = WeatherObservation(
            location_id=location_id, observed_at=weather.observed_at
        )
        _apply_fields(row, weather)
        session.add(row)
    else:
        _apply_fields(existing, weather)
        existing.observed_at = weather.observed_at

    history = WeatherObservationHistory(
        location_id=location_id, observed_at=weather.observed_at
    )
    _apply_fields(history, weather)
    session.add(history)


async def _replace_forecasts(
    session: AsyncSession, location_id: str, points: list[WeatherPoint]
) -> int:
    await session.execute(
        delete(WeatherForecast).where(WeatherForecast.location_id == location_id)
    )
    for point in points:
        row = WeatherForecast(location_id=location_id, forecast_at=point.observed_at)
        _apply_fields(row, point)
        session.add(row)
    return len(points)


async def _prune_history(session: AsyncSession) -> None:
    settings = get_settings()
    cutoff = datetime.now(tz=UTC) - timedelta(
        days=settings.weather_history_retention_days
    )
    await session.execute(
        delete(WeatherObservationHistory).where(
            WeatherObservationHistory.observed_at < cutoff
        )
    )


async def ingest_fixture_weather(session: AsyncSession) -> int:
    """Store deterministic current weather and forecasts for all locations."""
    result = await session.execute(select(Location))
    locations = result.scalars().all()
    total = 0
    for location in locations:
        await _upsert_observation(
            session, location.id, fixture_weather_for_location(location.id)
        )
        await _replace_forecasts(
            session, location.id, fixture_forecast_for_location(location.id)
        )
        total += 1
    await _prune_history(session)
    await session.commit()
    return total


async def ingest_openweather(session: AsyncSession) -> int:
    """Fetch current weather and forecast from OpenWeatherMap for all locations."""
    settings = get_settings()
    api_key = settings.require_openweather_api_key()
    client = OpenWeatherClient(api_key)
    total = 0

    try:
        result = await session.execute(select(Location))
        locations = result.scalars().all()
        for location in locations:
            try:
                weather = await client.get_current_weather(
                    location.latitude, location.longitude
                )
                forecasts = await client.get_forecast(
                    location.latitude, location.longitude
                )
            except OpenWeatherApiError as exc:
                logger.warning("OpenWeather fetch failed for %s: %s", location.id, exc)
                continue
            await _upsert_observation(session, location.id, weather)
            await _replace_forecasts(session, location.id, forecasts)
            total += 1
        await _prune_history(session)
        await session.commit()
    finally:
        await client.close()

    return total


async def run_weather_ingest() -> int:
    """Run weather ingestion according to configured data source."""
    settings = get_settings()
    factory = get_session_factory()

    async with factory() as session:
        source = settings.weather_data_source.lower()
        if source == "fixture":
            return await ingest_fixture_weather(session)
        if source == "openweather":
            return await ingest_openweather(session)
        raise ValueError(
            f"Unknown WEATHER_DATA_SOURCE={settings.weather_data_source!r}. "
            "Use fixture or openweather."
        )
