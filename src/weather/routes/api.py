"""REST API routes for Tight Lines / Fishing Brain integration."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.weather.db import get_session
from src.weather.schemas import (
    LocationRead,
    TideListResponse,
    WeatherAtRead,
    WeatherForecastResponse,
    WeatherRead,
)
from src.weather.services.tides import get_tides_for_location, list_locations
from src.weather.services.weather import (
    get_forecast_for_location,
    get_weather_at_time,
    get_weather_for_location,
)

router = APIRouter(prefix="/api", tags=["api"])


def _parse_iso_datetime(value: str, *, field_name: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail=f"Invalid {field_name} date format"
        ) from exc


@router.get("/locations", response_model=list[LocationRead])
async def api_list_locations(
    session: AsyncSession = Depends(get_session),
) -> list[LocationRead]:
    return await list_locations(session)


@router.get("/tides/{location_id}", response_model=TideListResponse)
async def api_get_tides(
    location_id: str,
    start: str = Query(..., description="ISO 8601 start datetime"),
    end: str = Query(..., description="ISO 8601 end datetime"),
    session: AsyncSession = Depends(get_session),
) -> TideListResponse:
    start_dt = _parse_iso_datetime(start, field_name="start")
    end_dt = _parse_iso_datetime(end, field_name="end")
    return await get_tides_for_location(session, location_id, start_dt, end_dt)


@router.get("/weather/{location_id}", response_model=WeatherRead)
async def api_get_weather(
    location_id: str,
    session: AsyncSession = Depends(get_session),
) -> WeatherRead:
    return await get_weather_for_location(session, location_id)


@router.get(
    "/weather/{location_id}/forecast",
    response_model=WeatherForecastResponse,
)
async def api_get_weather_forecast(
    location_id: str,
    start: str = Query(..., description="ISO 8601 start datetime"),
    end: str = Query(..., description="ISO 8601 end datetime"),
    session: AsyncSession = Depends(get_session),
) -> WeatherForecastResponse:
    start_dt = _parse_iso_datetime(start, field_name="start")
    end_dt = _parse_iso_datetime(end, field_name="end")
    return await get_forecast_for_location(session, location_id, start_dt, end_dt)


@router.get("/weather/{location_id}/at", response_model=WeatherAtRead)
async def api_get_weather_at(
    location_id: str,
    at: str = Query(..., description="ISO 8601 datetime to match"),
    session: AsyncSession = Depends(get_session),
) -> WeatherAtRead:
    at_dt = _parse_iso_datetime(at, field_name="at")
    return await get_weather_at_time(session, location_id, at_dt)
