"""Tide prediction queries for the REST API."""

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.weather.models import Location, TidePrediction
from src.weather.schemas import LocationRead, TideListResponse, TidePredictionRead


async def list_locations(session: AsyncSession) -> list[LocationRead]:
    result = await session.execute(select(Location).order_by(Location.name))
    locations = result.scalars().all()
    return [
        LocationRead(
            id=loc.id,
            name=loc.name,
            region=loc.region,
            latitude=loc.latitude,
            longitude=loc.longitude,
        )
        for loc in locations
    ]


async def get_tides_for_location(
    session: AsyncSession,
    location_id: str,
    start: datetime,
    end: datetime,
) -> TideListResponse:
    if start >= end:
        raise HTTPException(status_code=400, detail="start must be before end")

    location = await session.get(Location, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")

    result = await session.execute(
        select(TidePrediction)
        .where(
            TidePrediction.location_id == location_id,
            TidePrediction.prediction_time >= start,
            TidePrediction.prediction_time <= end,
        )
        .order_by(TidePrediction.prediction_time)
    )
    tides = result.scalars().all()

    return TideListResponse(
        tides=[
            TidePredictionRead(
                time=tide.prediction_time,
                type=tide.tide_type,
                height=float(tide.height_metres),
                phase=tide.tide_phase,
            )
            for tide in tides
        ]
    )
