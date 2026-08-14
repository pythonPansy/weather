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


class WeatherRead(BaseModel):
    summary: str | None = None
    wind_speed_mph: float | None = None
    wind_direction: str | None = None
    temperature_c: float | None = None
    conditions: str | None = None
    observed_at: datetime | None = None
