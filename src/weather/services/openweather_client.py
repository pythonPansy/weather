"""Client for OpenWeatherMap current weather API."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

from src.weather.config import OPENWEATHER_SIGNUP_URL

logger = logging.getLogger(__name__)

BASE_URL = "https://api.openweathermap.org"
MPS_TO_MPH = 2.2369362920544
COMPASS_8 = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


class OpenWeatherConfigError(ValueError):
    """Raised when OpenWeatherMap credentials are missing."""


class OpenWeatherApiError(RuntimeError):
    """Raised when the OpenWeatherMap API returns an error response."""


@dataclass(frozen=True)
class CurrentWeather:
    summary: str | None
    wind_speed_mph: float | None
    wind_direction: str | None
    temperature_c: float | None
    conditions: str | None
    observed_at: datetime


def metres_per_second_to_mph(speed_mps: float) -> float:
    return round(speed_mps * MPS_TO_MPH, 1)


def degrees_to_compass(degrees: float) -> str:
    """Map wind degrees to an 8-point compass (N centred on 0°)."""
    index = int((degrees % 360) / 45 + 0.5) % 8
    return COMPASS_8[index]


def build_summary(
    *,
    conditions: str | None,
    temperature_c: float | None,
    wind_direction: str | None,
    wind_speed_mph: float | None,
) -> str | None:
    parts: list[str] = []
    if conditions:
        parts.append(conditions)
    if temperature_c is not None:
        parts.append(f"{temperature_c}°C")
    wind_bits: list[str] = []
    if wind_direction:
        wind_bits.append(wind_direction)
    if wind_speed_mph is not None:
        wind_bits.append(f"{wind_speed_mph} mph")
    if wind_bits:
        parts.append(" ".join(wind_bits))
    return ", ".join(parts) if parts else None


def map_openweather_payload(payload: dict[str, Any]) -> CurrentWeather:
    weather_items = payload.get("weather") or []
    raw_description = None
    if weather_items:
        raw_description = weather_items[0].get("description")
    conditions = str(raw_description).strip().capitalize() if raw_description else None

    main = payload.get("main") or {}
    raw_temp = main.get("temp")
    temperature_c = round(float(raw_temp), 1) if raw_temp is not None else None

    wind = payload.get("wind") or {}
    raw_speed = wind.get("speed")
    wind_speed_mph = (
        metres_per_second_to_mph(float(raw_speed)) if raw_speed is not None else None
    )
    raw_deg = wind.get("deg")
    wind_direction = degrees_to_compass(float(raw_deg)) if raw_deg is not None else None

    raw_dt = payload.get("dt")
    if raw_dt is not None:
        observed_at = datetime.fromtimestamp(int(raw_dt), tz=UTC)
    else:
        observed_at = datetime.now(tz=UTC)

    summary = build_summary(
        conditions=conditions,
        temperature_c=temperature_c,
        wind_direction=wind_direction,
        wind_speed_mph=wind_speed_mph,
    )
    return CurrentWeather(
        summary=summary,
        wind_speed_mph=wind_speed_mph,
        wind_direction=wind_direction,
        temperature_c=temperature_c,
        conditions=conditions,
        observed_at=observed_at,
    )


class OpenWeatherClient:
    """HTTP client for OpenWeatherMap current weather."""

    def __init__(self, api_key: str, *, timeout: float = 30.0):
        if not api_key.strip():
            raise OpenWeatherConfigError(
                "OPENWEATHER_API_KEY is not set. Create a free key at "
                f"{OPENWEATHER_SIGNUP_URL} then add it to .env"
            )
        self._api_key = api_key
        self._client = httpx.AsyncClient(base_url=BASE_URL, timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def get_current_weather(
        self, latitude: float, longitude: float
    ) -> CurrentWeather:
        response = await self._client.get(
            "/data/2.5/weather",
            params={
                "lat": latitude,
                "lon": longitude,
                "appid": self._api_key,
                "units": "metric",
            },
        )
        _raise_for_status(response)
        return map_openweather_payload(response.json())


def _raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return
    if response.status_code == 401:
        raise OpenWeatherApiError(
            "OpenWeatherMap rejected the API key (401). "
            f"Check OPENWEATHER_API_KEY from {OPENWEATHER_SIGNUP_URL}"
        )
    raise OpenWeatherApiError(
        f"OpenWeatherMap API error {response.status_code}: {response.text[:200]}"
    )
