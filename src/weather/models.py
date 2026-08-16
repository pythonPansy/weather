"""SQLAlchemy ORM models for locations, tides, and weather."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
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
    weather_history: Mapped[list["WeatherObservationHistory"]] = relationship(
        back_populates="location"
    )
    weather_forecasts: Mapped[list["WeatherForecast"]] = relationship(
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


class _WeatherFieldsMixin:
    """Shared weather column definitions for latest / history / forecast rows."""

    summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    wind_speed_mph: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    wind_direction: Mapped[str | None] = mapped_column(String(8), nullable=True)
    temperature_c: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    conditions: Mapped[str | None] = mapped_column(String(120), nullable=True)
    pressure_hpa: Mapped[Decimal | None] = mapped_column(Numeric(6, 1), nullable=True)
    cloud_cover_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    humidity_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    moon_phase: Mapped[str | None] = mapped_column(String(32), nullable=True)
    swell_height_m: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    swell_period_s: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    swell_direction: Mapped[str | None] = mapped_column(String(8), nullable=True)


class WeatherObservation(_WeatherFieldsMixin, Base):
    """Latest observation per location (Tight Lines current-weather endpoint)."""

    __tablename__ = "weather_observations"

    location_id: Mapped[str] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), primary_key=True
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    location: Mapped[Location] = relationship(back_populates="weather_observation")


class WeatherObservationHistory(_WeatherFieldsMixin, Base):
    """Rolling observation history for nearest-at-time lookups."""

    __tablename__ = "weather_observation_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    location_id: Mapped[str] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    location: Mapped[Location] = relationship(back_populates="weather_history")


class WeatherForecast(_WeatherFieldsMixin, Base):
    """Forecast timesteps per location (OWM free tier is ~3-hourly, ~5 days)."""

    __tablename__ = "weather_forecasts"
    __table_args__ = (
        UniqueConstraint(
            "location_id",
            "forecast_at",
            name="uq_weather_forecasts_location_forecast_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    location_id: Mapped[str] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    forecast_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    location: Mapped[Location] = relationship(back_populates="weather_forecasts")
