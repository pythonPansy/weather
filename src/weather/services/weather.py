"""Weather queries for current, forecast range, and nearest-at-time APIs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.weather.config import get_settings
from src.weather.models import (
    Location,
    WeatherForecast,
    WeatherObservation,
    WeatherObservationHistory,
)
from src.weather.schemas import (
    WeatherAtRead,
    WeatherForecastPoint,
    WeatherForecastResponse,
    WeatherRead,
)


def _as_float(value: object | None) -> float | None:
    if value is None:
        return None
    return float(value)  # type: ignore[arg-type]


def _as_int(value: object | None) -> int | None:
    if value is None:
        return None
    return int(value)  # type: ignore[arg-type]


def _weather_fields(row: object) -> dict[str, object | None]:
    return {
        "summary": getattr(row, "summary", None),
        "wind_speed_mph": _as_float(getattr(row, "wind_speed_mph", None)),
        "wind_direction": getattr(row, "wind_direction", None),
        "temperature_c": _as_float(getattr(row, "temperature_c", None)),
        "conditions": getattr(row, "conditions", None),
        "pressure_hpa": _as_float(getattr(row, "pressure_hpa", None)),
        "cloud_cover_pct": _as_int(getattr(row, "cloud_cover_pct", None)),
        "humidity_pct": _as_int(getattr(row, "humidity_pct", None)),
        "moon_phase": getattr(row, "moon_phase", None),
        "swell_height_m": _as_float(getattr(row, "swell_height_m", None)),
        "swell_period_s": _as_float(getattr(row, "swell_period_s", None)),
        "swell_direction": getattr(row, "swell_direction", None),
    }


async def _require_location(session: AsyncSession, location_id: str) -> Location:
    location = await session.get(Location, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


async def get_weather_for_location(
    session: AsyncSession, location_id: str
) -> WeatherRead:
    await _require_location(session, location_id)

    observation = await session.get(WeatherObservation, location_id)
    if observation is None:
        raise HTTPException(status_code=503, detail="Weather observation not available")

    return WeatherRead(
        **_weather_fields(observation),
        observed_at=observation.observed_at,
    )


async def get_forecast_for_location(
    session: AsyncSession,
    location_id: str,
    start: datetime,
    end: datetime,
) -> WeatherForecastResponse:
    await _require_location(session, location_id)
    if end < start:
        raise HTTPException(status_code=400, detail="end must be on or after start")

    result = await session.execute(
        select(WeatherForecast)
        .where(
            WeatherForecast.location_id == location_id,
            WeatherForecast.forecast_at >= start,
            WeatherForecast.forecast_at <= end,
        )
        .order_by(WeatherForecast.forecast_at.asc())
    )
    rows = result.scalars().all()
    return WeatherForecastResponse(
        forecasts=[
            WeatherForecastPoint(
                **_weather_fields(row),
                forecast_at=row.forecast_at,
            )
            for row in rows
        ]
    )


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


async def get_weather_at_time(
    session: AsyncSession,
    location_id: str,
    at: datetime,
) -> WeatherAtRead:
    await _require_location(session, location_id)
    at = _as_aware(at)

    settings = get_settings()
    tolerance = timedelta(hours=settings.weather_at_tolerance_hours)
    window_start = at - tolerance
    window_end = at + tolerance

    history_result = await session.execute(
        select(WeatherObservationHistory).where(
            WeatherObservationHistory.location_id == location_id,
            WeatherObservationHistory.observed_at >= window_start,
            WeatherObservationHistory.observed_at <= window_end,
        )
    )
    history_rows = list(history_result.scalars().all())

    forecast_result = await session.execute(
        select(WeatherForecast).where(
            WeatherForecast.location_id == location_id,
            WeatherForecast.forecast_at >= window_start,
            WeatherForecast.forecast_at <= window_end,
        )
    )
    forecast_rows = list(forecast_result.scalars().all())

    candidates: list[tuple[datetime, str, object]] = []
    for row in history_rows:
        candidates.append((_as_aware(row.observed_at), "observation", row))
    for row in forecast_rows:
        candidates.append((_as_aware(row.forecast_at), "forecast", row))

    # Also consider the latest observation if it falls in the window.
    latest = await session.get(WeatherObservation, location_id)
    if latest is not None:
        latest_at = _as_aware(latest.observed_at)
        if window_start <= latest_at <= window_end:
            candidates.append((latest_at, "observation", latest))

    if not candidates:
        return WeatherAtRead(available=False)

    best_stamp, best_source, best_row = min(
        candidates, key=lambda item: abs((item[0] - at).total_seconds())
    )
    delta = int((best_stamp - at).total_seconds())
    return WeatherAtRead(
        available=True,
        matched_at=best_stamp,
        delta_seconds=delta,
        source=best_source,
        observed_at=best_stamp if best_source == "observation" else None,
        **_weather_fields(best_row),
    )
