import requests

from ...context import PipelineContext
from ...logging_config import get_logger
from ..base import BaseTask
from ..registry import register_task

logger = get_logger(__name__)

TIDETURTLE_TIDES_URL = "https://tideturtle.com/api/v1/tides"


def normalise_tides_response(payload: dict) -> dict:
    """Map TideTurtle JSON into the project's UK-English schema."""
    place = payload.get("place") or {}
    tides = payload.get("tides") or {}
    data = tides.get("data") or {}

    extrema = [
        {
            "time": item["time"],
            "date": item["date"],
            "height_m": item["height"],
            "is_high": item["isHigh"],
        }
        for item in data.get("extrema") or []
    ]

    return {
        "distance_km": payload.get("distanceKm"),
        "place": {
            "slug": place.get("slug"),
            "country": place.get("country"),
            "region": place.get("region"),
            "name": place.get("name"),
            "country_name": place.get("country_name"),
            "region_name": place.get("region_name"),
            "href": place.get("href"),
            "latitude": place.get("lat"),
            "longitude": place.get("lon"),
        },
        "datum": data.get("datum"),
        "unit": data.get("unit"),
        "time_zone": data.get("timezone"),
        "source": data.get("source"),
        "extrema": extrema,
        "licence": tides.get("license"),
    }


@register_task("tides_api")
class TidesAPITask(BaseTask):
    def __init__(self, params: dict):
        self.params = params

    def run(self, context: PipelineContext) -> PipelineContext:
        lat = self.params["latitude"]
        lon = self.params["longitude"]

        logger.info("Fetching tides for lat=%s lon=%s", lat, lon)
        response = requests.get(
            TIDETURTLE_TIDES_URL,
            params={"lat": lat, "lon": lon},
            timeout=30,
        )
        response.raise_for_status()

        return context.with_values(
            tides_call={
                "latitude": lat,
                "longitude": lon,
            },
            tides=normalise_tides_response(response.json()),
        )
