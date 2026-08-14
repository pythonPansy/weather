"""Current weather queries for the REST API."""

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.weather.models import Location, WeatherObservation
from src.weather.schemas import WeatherRead


def _as_float(value: object | None) -> float | None:
    if value is None:
        return None
    return float(value)  # type: ignore[arg-type]


async def get_weather_for_location(
    session: AsyncSession, location_id: str
) -> WeatherRead:
    location = await session.get(Location, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")

    observation = await session.get(WeatherObservation, location_id)
    if observation is None:
        raise HTTPException(status_code=503, detail="Weather observation not available")

    return WeatherRead(
        summary=observation.summary,
        wind_speed_mph=_as_float(observation.wind_speed_mph),
        wind_direction=observation.wind_direction,
        temperature_c=_as_float(observation.temperature_c),
        conditions=observation.conditions,
        observed_at=observation.observed_at,
    )
