"""Pydantic schemas matching the Tight Lines integration spec."""

from datetime import datetime

from pydantic import BaseModel, Field


class LocationRead(BaseModel):
    id: str
    name: str
    region: str
    latitude: float
    longitude: float


class TidePredictionRead(BaseModel):
    time: datetime
    type: str = Field(pattern="^(high|low)$")
    height: float
    phase: str | None = Field(default=None)


class TideListResponse(BaseModel):
    tides: list[TidePredictionRead]
