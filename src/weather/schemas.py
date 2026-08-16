"""Pydantic schemas matching the Tight Lines / Fishing Brain integration spec."""

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


class WeatherFields(BaseModel):
    """Shared weather / marine fields (nullable when unknown)."""

    summary: str | None = None
    wind_speed_mph: float | None = None
    wind_direction: str | None = None
    temperature_c: float | None = None
    conditions: str | None = None
    pressure_hpa: float | None = None
    cloud_cover_pct: int | None = None
    humidity_pct: int | None = None
    moon_phase: str | None = None
    swell_height_m: float | None = None
    swell_period_s: float | None = None
    swell_direction: str | None = None


class WeatherRead(WeatherFields):
    observed_at: datetime | None = None


class WeatherAtRead(WeatherFields):
    """Nearest stored observation or forecast to a requested timestamp."""

    available: bool = True
    matched_at: datetime | None = None
    delta_seconds: int | None = None
    source: str | None = Field(
        default=None, description="observation | forecast | null when unavailable"
    )
    observed_at: datetime | None = None


class WeatherForecastPoint(WeatherFields):
    forecast_at: datetime


class WeatherForecastResponse(BaseModel):
    forecasts: list[WeatherForecastPoint]
