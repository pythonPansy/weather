"""Business logic for tide locations and predictions."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import requests
import yaml

from ..logging_config import get_logger
from .models import Location, TideEvent, TidePredictions

logger = get_logger(__name__)

TIDETURTLE_TIDES_URL = "https://tideturtle.com/api/v1/tides"


def load_locations(config_path: str | Path = "config/locations.yaml") -> list[Location]:
    """Load tide locations from YAML config.

    Args:
        config_path: Path to locations YAML config file

    Returns:
        List of Location objects

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Locations config not found: {config_path}")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    if not data or "locations" not in data:
        raise ValueError("Invalid locations config: missing 'locations' key")

    return [Location(**loc) for loc in data["locations"]]


def classify_tide_phase(height: float, is_high: bool) -> str | None:
    """Classify tide phase based on height.

    This is a simplified classification based on tide height.
    In a production system, this would use historical data or astronomical
    calculations to determine spring/neap cycles.

    Args:
        height: Tide height in metres
        is_high: True if high tide, False if low tide

    Returns:
        "spring", "neap", "medium", or None if classification unavailable
    """
    if not is_high:
        # For low tides, classify based on how low they are
        if height < 1.0:
            return "spring"  # Very low = spring tide
        elif height > 2.0:
            return "neap"  # Not very low = neap tide
        else:
            return "medium"
    else:
        # For high tides, classify based on how high they are
        if height > 4.5:
            return "spring"  # Very high = spring tide
        elif height < 3.5:
            return "neap"  # Not very high = neap tide
        else:
            return "medium"


def get_tide_predictions(
    location_id: str,
    start: datetime,
    end: datetime,
    locations: list[Location],
) -> TidePredictions:
    """Fetch tide predictions for a location and date range.

    Args:
        location_id: Location ID from locations config
        start: Start date/time for predictions
        end: End date/time for predictions
        locations: List of available locations

    Returns:
        TidePredictions with tide events

    Raises:
        ValueError: If location_id not found
        requests.RequestException: If API call fails
    """
    # Find the location
    location = next((loc for loc in locations if loc.id == location_id), None)
    if not location:
        raise ValueError(f"Location not found: {location_id}")

    logger.info(
        "Fetching tides for %s (lat=%s, lon=%s) from %s to %s",
        location_id,
        location.latitude,
        location.longitude,
        start.isoformat(),
        end.isoformat(),
    )

    # Call TideTurtle API
    response = requests.get(
        TIDETURTLE_TIDES_URL,
        params={"lat": location.latitude, "lon": location.longitude},
        timeout=30,
    )
    response.raise_for_status()

    # Parse response
    data = response.json()
    tides_data = data.get("tides", {}).get("data", {})
    extrema = tides_data.get("extrema", [])

    # Convert to TideEvent objects and filter by date range
    tide_events = []
    for item in extrema:
        # Parse time - TideTurtle returns ISO 8601 format with milliseconds
        time_str = item["time"]
        # Remove milliseconds if present (.000Z -> Z)
        if "." in time_str:
            time_str = time_str.split(".")[0] + "Z"
        tide_time = datetime.fromisoformat(time_str.replace("Z", "+00:00"))

        # Filter by date range
        if not (start <= tide_time <= end):
            continue

        is_high = item["isHigh"]
        height = item["height"]

        tide_events.append(
            TideEvent(
                time=tide_time,
                type="high" if is_high else "low",
                height=height,
                phase=classify_tide_phase(height, is_high),
            )
        )

    return TidePredictions(tides=tide_events)
