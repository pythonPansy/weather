import requests
from .base import BaseTask
from .registry import register_task

@register_task("weather_api")
class WeatherAPITask(BaseTask):
    def __init__(self, params: dict):
        self.params = params

    def run(self, context: dict) -> dict:
        api_key = self.params["api_key"]
        lat = self.params["latitude"]
        lon = self.params["longitude"]
        base_url = "https://api.openweathermap.org/data/2.5/weather?"
        complete_url = f'{base_url}&lat={lat}&lon={lon}&appid={api_key}'

        response = requests.get(complete_url)
        response.raise_for_status()

        context["weather"] = response.json()
        return context


# api_key = "8059da9872aefd0642e3e9100993ee37"


# latitude:str = "50.547"
# longitude:str = "-3.497"

