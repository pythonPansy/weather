import requests

from ...context import PipelineContext
from ...logging_config import get_logger
from ..base import BaseTask
from ..registry import register_task

logger = get_logger(__name__)

OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


@register_task("weather_forecast_api")
class WeatherForecastAPITask(BaseTask):
    def __init__(self, params: dict):
        self.params = params

    def run(self, context: PipelineContext) -> PipelineContext:
        api_key = self.params["api_key"]
        lat = self.params["latitude"]
        lon = self.params["longitude"]

        logger.info("Fetching weather forecast for lat=%s lon=%s", lat, lon)
        response = requests.get(
            OPENWEATHER_FORECAST_URL,
            params={"lat": lat, "lon": lon, "appid": api_key},
            timeout=30,
        )
        response.raise_for_status()

        return context.with_values(
            weather_forecast_call={
                "latitude": lat,
                "longitude": lon,
            },
            weather_forecast=response.json(),
        )
