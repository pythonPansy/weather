import os

import pytest

from src.tasks.ingest.weather_api import WeatherAPITask
from tests.helpers import print_weather_response

pytestmark = pytest.mark.live_api


@pytest.mark.skipif(
    not os.environ.get("OPENWEATHER_API_KEY"),
    reason="OPENWEATHER_API_KEY not set",
)
def test_weather_task_calls_openweather_api():
    task = WeatherAPITask(
        params={
            "latitude": 45.0,
            "longitude": -73.0,
            "api_key": os.environ["OPENWEATHER_API_KEY"],
        }
    )

    result = task.run({})

    print_weather_response(result["weather"])

    assert "weather" in result
    weather = result["weather"]
    assert "main" in weather
    assert isinstance(weather["main"]["temp"], (int, float))
