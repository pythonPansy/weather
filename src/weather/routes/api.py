"""REST API routes for Tight Lines integration."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.weather.db import get_session
from src.weather.schemas import LocationRead, TideListResponse, WeatherRead
from src.weather.services.tides import get_tides_for_location, list_locations
from src.weather.services.weather import get_weather_for_location

router = APIRouter(prefix="/api", tags=["api"])


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
    try:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid date format") from exc

    return await get_tides_for_location(session, location_id, start_dt, end_dt)


@router.get("/weather/{location_id}", response_model=WeatherRead)
async def api_get_weather(
    location_id: str,
    session: AsyncSession = Depends(get_session),
) -> WeatherRead:
    return await get_weather_for_location(session, location_id)
