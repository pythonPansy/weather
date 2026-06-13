import requests

from ...logging_config import get_logger
from ..base import BaseTask
from ..registry import register_task

logger = get_logger(__name__)


@register_task("weather_api")
class WeatherAPITask(BaseTask):
    def __init__(self, params: dict):
        self.params = params

    def run(self, context: dict) -> dict:
        api_key = self.params["api_key"]
        lat = self.params["latitude"]
        lon = self.params["longitude"]
        base_url = "https://api.openweathermap.org/data/2.5/weather?"
        complete_url = f"{base_url}&lat={lat}&lon={lon}&appid={api_key}"

        logger.info("Fetching weather for lat=%s lon=%s", lat, lon)
        response = requests.get(complete_url)
        response.raise_for_status()

        context["weather_call"] = {
            "latitude": lat,
            "longitude": lon,
        }
        context["weather"] = response.json()
        return context
