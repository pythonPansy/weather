"""SQLAlchemy ORM models for locations, tides, and current weather."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.weather.db import Base


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    region: Mapped[str] = mapped_column(String(120), nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    mhws: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    mhwn: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    admiralty_station_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    admiralty_station_name: Mapped[str | None] = mapped_column(
        String(120), nullable=True
    )

    tides: Mapped[list["TidePrediction"]] = relationship(back_populates="location")
    weather_observation: Mapped["WeatherObservation | None"] = relationship(
        back_populates="location"
    )


class TidePrediction(Base):
    __tablename__ = "tide_predictions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    location_id: Mapped[str] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), nullable=False
    )
    prediction_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    tide_type: Mapped[str] = mapped_column(String(8), nullable=False)
    height_metres: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    tide_phase: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    location: Mapped[Location] = relationship(back_populates="tides")


class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    location_id: Mapped[str] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), primary_key=True
    )
    summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    wind_speed_mph: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    wind_direction: Mapped[str | None] = mapped_column(String(8), nullable=True)
    temperature_c: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    conditions: Mapped[str | None] = mapped_column(String(120), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    location: Mapped[Location] = relationship(back_populates="weather_observation")
