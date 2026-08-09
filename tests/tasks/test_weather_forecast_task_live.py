import os

import pytest

from src.context import PipelineContext
from src.tasks.ingest.weather_forecast_api import WeatherForecastAPITask

pytestmark = pytest.mark.live_api


@pytest.mark.skipif(
    not os.environ.get("OPENWEATHER_API_KEY"),
    reason="OPENWEATHER_API_KEY not set",
)
def test_weather_forecast_task_calls_openweather_api():
    task = WeatherForecastAPITask(
        params={
            "latitude": 45.0,
            "longitude": -73.0,
            "api_key": os.environ["OPENWEATHER_API_KEY"],
        }
    )

    result = task.run(PipelineContext())

    assert result.weather_forecast is not None
    forecast = result.weather_forecast
    assert "list" in forecast
    assert isinstance(forecast["list"], list)
    assert len(forecast["list"]) > 0
    assert "main" in forecast["list"][0]
