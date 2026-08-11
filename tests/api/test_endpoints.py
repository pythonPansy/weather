"""Tests for API endpoints."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.models import Location, TideEvent, TidePredictions


@pytest.fixture
def client():
    """Create a test client for the API."""
    # Use context manager to ensure lifespan is triggered
    with TestClient(app) as client:
        yield client


def test_list_locations(client):
    """Test GET /api/locations returns location list."""
    response = client.get("/api/locations")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0

    # Check first location has required fields
    first_loc = data[0]
    assert "id" in first_loc
    assert "name" in first_loc
    assert "region" in first_loc
    assert "latitude" in first_loc
    assert "longitude" in first_loc


def test_list_locations_schema(client):
    """Test GET /api/locations returns valid Location objects."""
    response = client.get("/api/locations")
    data = response.json()

    # Validate each location can be parsed as Location model
    for loc_data in data:
        loc = Location(**loc_data)
        assert loc.id
        assert loc.name
        assert loc.region
        assert isinstance(loc.latitude, float)
        assert isinstance(loc.longitude, float)


def test_get_tides_mocked(client, mocker):
    """Test GET /api/tides/{location_id} with mocked service."""
    # Mock the service function
    mock_predictions = TidePredictions(
        tides=[
            TideEvent(
                time=datetime(2026, 8, 11, 5, 23, 0),
                type="high",
                height=4.8,
                phase="spring",
            ),
            TideEvent(
                time=datetime(2026, 8, 11, 11, 42, 0),
                type="low",
                height=1.2,
                phase="spring",
            ),
        ]
    )

    mocker.patch(
        "src.api.main.get_tide_predictions",
        return_value=mock_predictions,
    )

    response = client.get(
        "/api/tides/plym-uk-001",
        params={
            "start": "2026-08-11T00:00:00Z",
            "end": "2026-08-18T23:59:59Z",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "tides" in data
    assert len(data["tides"]) == 2

    first_tide = data["tides"][0]
    assert first_tide["type"] in ["high", "low"]
    assert isinstance(first_tide["height"], (int, float))
    assert first_tide["phase"] in ["spring", "neap", "medium", None]


def test_get_tides_invalid_location(client, mocker):
    """Test GET /api/tides/{location_id} with invalid location returns 404."""
    mocker.patch(
        "src.api.main.get_tide_predictions",
        side_effect=ValueError("Location not found: invalid-id"),
    )

    response = client.get(
        "/api/tides/invalid-id",
        params={
            "start": "2026-08-11T00:00:00Z",
            "end": "2026-08-18T23:59:59Z",
        },
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_tides_missing_params(client):
    """Test GET /api/tides/{location_id} without required params returns 422."""
    response = client.get("/api/tides/plym-uk-001")

    # FastAPI returns 422 for missing required query parameters
    assert response.status_code == 422


def test_get_tides_invalid_date_format(client):
    """Test GET /api/tides/{location_id} with invalid date format returns 422."""
    response = client.get(
        "/api/tides/plym-uk-001",
        params={
            "start": "invalid-date",
            "end": "2026-08-18T23:59:59Z",
        },
    )

    # FastAPI returns 422 for invalid date format
    assert response.status_code == 422


@pytest.mark.live_api
def test_get_tides_live(client):
    """Test GET /api/tides/{location_id} with live API call."""
    response = client.get(
        "/api/tides/plym-uk-001",
        params={
            "start": "2026-08-11T00:00:00Z",
            "end": "2026-08-18T23:59:59Z",
        },
    )

    # May fail if API is down, but that's expected for live tests
    if response.status_code == 200:
        data = response.json()
        assert "tides" in data

        # Check each tide has required fields and valid values
        for tide in data["tides"]:
            assert "time" in tide
            assert "type" in tide
            assert tide["type"] in ["high", "low"]
            assert "height" in tide
            assert isinstance(tide["height"], (int, float))
            assert "phase" in tide
            if tide["phase"] is not None:
                assert tide["phase"] in ["spring", "neap", "medium"]
