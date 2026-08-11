"""Pydantic models for API request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Location(BaseModel):
    """A tide location with geographic coordinates."""

    id: str = Field(..., description="Unique identifier for this location")
    name: str = Field(..., description="Human-readable location name")
    region: str = Field(..., description="Geographic region")
    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees")


class TideEvent(BaseModel):
    """A single tide event (high or low)."""

    time: datetime = Field(
        ..., description="Date/time of tide event in ISO 8601 format"
    )
    type: Literal["high", "low"] = Field(..., description="Tide type")
    height: float = Field(..., description="Tide height in metres")
    phase: Literal["spring", "neap", "medium"] | None = Field(
        ..., description="Tide phase classification"
    )


class TidePredictions(BaseModel):
    """Tide predictions for a location."""

    tides: list[TideEvent] = Field(..., description="List of tide events")
