from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.weather.services.openweather_client import (
    OpenWeatherApiError,
    OpenWeatherClient,
    OpenWeatherConfigError,
    build_summary,
    degrees_to_compass,
    map_openweather_payload,
    metres_per_second_to_mph,
)

CANNED_OBSERVED_AT = datetime(2026, 8, 14, 7, 0, tzinfo=UTC)
CANNED_OWM_PAYLOAD = {
    "weather": [{"id": 800, "main": "Clear", "description": "clear sky"}],
    "main": {"temp": 12.04, "feels_like": 11.0},
    "wind": {"speed": 3.576, "deg": 225},
    "dt": int(CANNED_OBSERVED_AT.timestamp()),
}


def test_metres_per_second_to_mph() -> None:
    assert metres_per_second_to_mph(3.576) == 8.0


def test_degrees_to_compass() -> None:
    assert degrees_to_compass(0) == "N"
    assert degrees_to_compass(45) == "NE"
    assert degrees_to_compass(22.4) == "N"
    assert degrees_to_compass(22.5) == "NE"
    assert degrees_to_compass(225) == "SW"
    assert degrees_to_compass(337.5) == "N"
    assert degrees_to_compass(360) == "N"


def test_build_summary_omits_missing_parts() -> None:
    assert (
        build_summary(
            conditions="Clear sky",
            temperature_c=12.0,
            wind_direction="SW",
            wind_speed_mph=8.0,
        )
        == "Clear sky, 12.0°C, SW 8.0 mph"
    )
    assert (
        build_summary(
            conditions="Clear sky",
            temperature_c=None,
            wind_direction=None,
            wind_speed_mph=None,
        )
        == "Clear sky"
    )
    assert (
        build_summary(
            conditions=None,
            temperature_c=None,
            wind_direction=None,
            wind_speed_mph=None,
        )
        is None
    )


def test_map_openweather_payload() -> None:
    mapped = map_openweather_payload(CANNED_OWM_PAYLOAD)
    assert mapped.conditions == "Clear sky"
    assert mapped.temperature_c == 12.0
    assert mapped.wind_speed_mph == 8.0
    assert mapped.wind_direction == "SW"
    assert mapped.observed_at == CANNED_OBSERVED_AT
    assert mapped.summary == "Clear sky, 12.0°C, SW 8.0 mph"


def test_map_openweather_payload_missing_wind() -> None:
    mapped = map_openweather_payload(
        {
            "weather": [{"description": "light rain"}],
            "main": {"temp": 9.0},
            "dt": 1692000000,
        }
    )
    assert mapped.wind_direction is None
    assert mapped.wind_speed_mph is None
    assert mapped.summary == "Light rain, 9.0°C"


def test_client_requires_api_key() -> None:
    with pytest.raises(OpenWeatherConfigError):
        OpenWeatherClient("")


@pytest.mark.asyncio
async def test_get_current_weather_parses_response() -> None:
    client = OpenWeatherClient("test-key")
    mock_response = AsyncMock()
    mock_response.is_success = True
    mock_response.json = lambda: CANNED_OWM_PAYLOAD

    with patch.object(client._client, "get", return_value=mock_response) as mock_get:
        weather = await client.get_current_weather(50.3755, -4.1427)

    mock_get.assert_awaited_once()
    params = mock_get.await_args.kwargs["params"]
    assert params["lat"] == 50.3755
    assert params["lon"] == -4.1427
    assert params["appid"] == "test-key"
    assert params["units"] == "metric"
    assert weather.wind_direction == "SW"
    await client.close()


@pytest.mark.asyncio
async def test_unauthorised_raises_clear_error() -> None:
    client = OpenWeatherClient("bad-key")
    mock_response = AsyncMock()
    mock_response.is_success = False
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"

    with patch.object(client._client, "get", return_value=mock_response):
        with pytest.raises(OpenWeatherApiError, match="API key"):
            await client.get_current_weather(50.0, -4.0)

    await client.close()
