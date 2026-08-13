"""Client for UKHO Admiralty UK Tidal API (Discovery tier)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://admiraltyapi.azure-api.net/uktidalapi"
SIGNUP_URL = "https://developer.admiralty.co.uk/product#product=uk-tidal-api"


class AdmiraltyConfigError(ValueError):
    """Raised when Admiralty API credentials or configuration are missing."""


class AdmiraltyApiError(RuntimeError):
    """Raised when the Admiralty API returns an error response."""


@dataclass(frozen=True)
class AdmiraltyStation:
    station_id: str
    name: str


@dataclass(frozen=True)
class AdmiraltyTidalEvent:
    event_time: datetime
    event_type: str
    height_metres: float


def _parse_event_time(value: str) -> datetime:
    normalised = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalised)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _normalise_tide_type(event_type: str) -> str:
    if event_type.lower() == "highwater":
        return "high"
    if event_type.lower() == "lowwater":
        return "low"
    raise ValueError(f"Unknown Admiralty event type: {event_type}")


class AdmiraltyClient:
    """HTTP client for Admiralty UK Tidal API Discovery."""

    def __init__(self, api_key: str, *, timeout: float = 30.0):
        if not api_key.strip():
            raise AdmiraltyConfigError(
                "ADMIRALTY_API_KEY is not set. Subscribe free at "
                f"{SIGNUP_URL} then add the primary subscription key to .env"
            )
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=timeout,
            headers={"Ocp-Apim-Subscription-Key": api_key},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def list_stations(self) -> list[AdmiraltyStation]:
        response = await self._client.get("/api/V1/Stations/")
        _raise_for_status(response)
        payload = response.json()
        stations: list[AdmiraltyStation] = []
        for feature in payload.get("features", []):
            props = feature.get("properties") or {}
            station_id = props.get("Id") or props.get("id")
            name = props.get("Name") or props.get("name")
            if station_id and name:
                stations.append(
                    AdmiraltyStation(station_id=str(station_id), name=str(name))
                )
        return stations

    async def get_tidal_events(
        self, station_id: str, *, duration_days: int = 7
    ) -> list[AdmiraltyTidalEvent]:
        if not 1 <= duration_days <= 7:
            raise ValueError("Discovery tier supports duration 1–7 days only")

        response = await self._client.get(
            f"/api/V1/Stations/{station_id}/TidalEvents",
            params={"duration": duration_days},
        )
        _raise_for_status(response)
        return [_parse_event(item) for item in response.json()]

    async def resolve_station_id(self, station_name: str) -> str | None:
        """Match a seed location name to an Admiralty station ID."""
        target = station_name.strip().lower()
        stations = await self.list_stations()

        for station in stations:
            if station.name.strip().lower() == target:
                return station.station_id

        for station in stations:
            admiralty_name = station.name.strip().lower()
            if target in admiralty_name or admiralty_name in target:
                return station.station_id

        logger.warning("No Admiralty station match for %r", station_name)
        return None


def _parse_event(item: dict[str, Any]) -> AdmiraltyTidalEvent:
    return AdmiraltyTidalEvent(
        event_time=_parse_event_time(item["DateTime"]),
        event_type=_normalise_tide_type(item["EventType"]),
        height_metres=float(item["Height"]),
    )


def _raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return
    if response.status_code == 401:
        raise AdmiraltyApiError(
            "Admiralty API rejected the subscription key (401). "
            f"Check ADMIRALTY_API_KEY from {SIGNUP_URL}"
        )
    if response.status_code == 403:
        raise AdmiraltyApiError(
            "Admiralty API quota exceeded (403). Discovery allows 10,000 calls/month."
        )
    raise AdmiraltyApiError(
        f"Admiralty API error {response.status_code}: {response.text[:200]}"
    )
