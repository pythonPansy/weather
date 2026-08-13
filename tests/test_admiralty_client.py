"""Tests for Admiralty UK Tidal API client."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.weather.services.admiralty_client import (
    AdmiraltyApiError,
    AdmiraltyClient,
    AdmiraltyConfigError,
)


def test_client_requires_api_key() -> None:
    with pytest.raises(AdmiraltyConfigError):
        AdmiraltyClient("")


@pytest.mark.asyncio
async def test_get_tidal_events_parses_response() -> None:
    client = AdmiraltyClient("test-key")
    mock_response = AsyncMock()
    mock_response.is_success = True
    mock_response.json = lambda: [
        {
            "EventType": "HighWater",
            "DateTime": "2026-08-13T07:54:00Z",
            "Height": 4.44,
        },
        {
            "EventType": "LowWater",
            "DateTime": "2026-08-13T13:41:00Z",
            "Height": 0.56,
        },
    ]

    with patch.object(client._client, "get", return_value=mock_response) as mock_get:
        events = await client.get_tidal_events("0068", duration_days=7)

    mock_get.assert_awaited_once()
    assert events[0].event_type == "high"
    assert events[0].height_metres == 4.44
    assert events[0].event_time == datetime(2026, 8, 13, 7, 54, tzinfo=UTC)
    await client.close()


@pytest.mark.asyncio
async def test_unauthorised_raises_clear_error() -> None:
    client = AdmiraltyClient("bad-key")
    mock_response = AsyncMock()
    mock_response.is_success = False
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"

    with patch.object(client._client, "get", return_value=mock_response):
        with pytest.raises(AdmiraltyApiError, match="subscription key"):
            await client.get_tidal_events("0068")

    await client.close()


@pytest.mark.asyncio
async def test_resolve_station_id_exact_match() -> None:
    client = AdmiraltyClient("test-key")
    stations_response = AsyncMock()
    stations_response.is_success = True
    stations_response.json = lambda: {
        "features": [
            {
                "properties": {
                    "Id": "0123",
                    "Name": "Minehead",
                }
            }
        ]
    }

    with patch.object(client._client, "get", return_value=stations_response):
        station_id = await client.resolve_station_id("Minehead")

    assert station_id == "0123"
    await client.close()
