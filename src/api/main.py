"""FastAPI application for tide locations and predictions."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from ..logging_config import get_logger
from .models import Location, TidePredictions
from .services import get_tide_predictions, load_locations

logger = get_logger(__name__)

# Load locations at startup
LOCATIONS: list[Location] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load locations configuration on startup and cleanup on shutdown."""
    global LOCATIONS
    try:
        config_path = Path(__file__).parent.parent.parent / "config" / "locations.yaml"
        LOCATIONS = load_locations(config_path)
        logger.info("Loaded %d tide locations", len(LOCATIONS))
    except Exception as e:
        logger.error("Failed to load locations: %s", e)
        raise
    yield
    # Cleanup can go here if needed


app = FastAPI(
    title="Weather App API",
    version="1.0.0",
    description="Tide predictions and location data",
    lifespan=lifespan,
)


@app.get("/api/locations", response_model=list[Location])
async def list_locations() -> list[Location]:
    """Return all available tide locations.

    Returns a list of locations with id, name, region, latitude, and longitude.
    """
    return LOCATIONS


@app.get("/api/tides/{location_id}", response_model=TidePredictions)
async def get_tides(
    location_id: str,
    start: datetime = Query(
        ...,
        description="Start date/time for predictions (ISO 8601)",
        examples=["2026-08-11T00:00:00Z"],
    ),
    end: datetime = Query(
        ...,
        description="End date/time for predictions (ISO 8601)",
        examples=["2026-08-18T23:59:59Z"],
    ),
) -> TidePredictions:
    """Return tide predictions for a specific location and date range.

    Args:
        location_id: Location ID from /api/locations endpoint
        start: Start date/time for predictions (ISO 8601 format)
        end: End date/time for predictions (ISO 8601 format)

    Returns:
        Tide predictions with time, type, height, and phase for each tide event

    Raises:
        404: Location ID not found
        400: Invalid date format or date range
        500: Failed to retrieve tide data
    """
    try:
        predictions = get_tide_predictions(location_id, start, end, LOCATIONS)
        return predictions
    except ValueError as e:
        logger.warning("Location not found: %s", location_id)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to fetch tide predictions for %s", location_id)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve tide data: {e}"
        )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors as 400 Bad Request."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )
