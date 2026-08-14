"""Current-weather ingestion — fixture mode and OpenWeatherMap refresh."""

import logging
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.weather.config import get_settings
from src.weather.db import get_session_factory
from src.weather.models import Location, WeatherObservation
from src.weather.services.openweather_client import (
    CurrentWeather,
    OpenWeatherApiError,
    OpenWeatherClient,
    build_summary,
)

logger = logging.getLogger(__name__)

_COMPASS_8 = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


def fixture_weather_for_location(location_id: str) -> CurrentWeather:
    """Deterministic observation derived from the location id."""
    seed = sum(ord(character) for character in location_id)
    temperature_c = round(10.0 + (seed % 8), 1)
    wind_speed_mph = round(6.0 + (seed % 10), 1)
    wind_direction = _COMPASS_8[seed % 8]
    conditions = "Partly cloudy"
    return CurrentWeather(
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
        observed_at=datetime.now(tz=UTC).replace(second=0, microsecond=0),
    )


def _to_decimal(value: float | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


async def _upsert_observation(
    session: AsyncSession, location_id: str, weather: CurrentWeather
) -> None:
    existing = await session.get(WeatherObservation, location_id)
    if existing is None:
        session.add(
            WeatherObservation(
                location_id=location_id,
                summary=weather.summary,
                wind_speed_mph=_to_decimal(weather.wind_speed_mph),
                wind_direction=weather.wind_direction,
                temperature_c=_to_decimal(weather.temperature_c),
                conditions=weather.conditions,
                observed_at=weather.observed_at,
            )
        )
        return

    existing.summary = weather.summary
    existing.wind_speed_mph = _to_decimal(weather.wind_speed_mph)
    existing.wind_direction = weather.wind_direction
    existing.temperature_c = _to_decimal(weather.temperature_c)
    existing.conditions = weather.conditions
    existing.observed_at = weather.observed_at


async def ingest_fixture_weather(session: AsyncSession) -> int:
    """Store deterministic current weather for all locations."""
    result = await session.execute(select(Location))
    locations = result.scalars().all()
    total = 0
    for location in locations:
        await _upsert_observation(
            session, location.id, fixture_weather_for_location(location.id)
        )
        total += 1
    await session.commit()
    return total


async def ingest_openweather(session: AsyncSession) -> int:
    """Fetch current weather from OpenWeatherMap for all locations."""
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
            except OpenWeatherApiError as exc:
                logger.warning("OpenWeather fetch failed for %s: %s", location.id, exc)
                continue
            await _upsert_observation(session, location.id, weather)
            total += 1
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
