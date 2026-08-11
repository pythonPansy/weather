"""Tests for API service layer."""

from datetime import datetime
from pathlib import Path

import pytest

from src.api.models import Location
from src.api.services import classify_tide_phase, load_locations


def test_load_locations():
    """Test loading locations from YAML config."""
    config_path = Path(__file__).parent.parent.parent / "config" / "locations.yaml"
    locations = load_locations(config_path)

    assert len(locations) > 0
    assert all(isinstance(loc, Location) for loc in locations)

    # Check first location has required fields
    first_loc = locations[0]
    assert first_loc.id
    assert first_loc.name
    assert first_loc.region
    assert isinstance(first_loc.latitude, float)
    assert isinstance(first_loc.longitude, float)


def test_load_locations_missing_file():
    """Test loading locations from non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_locations("nonexistent.yaml")


def test_classify_tide_phase_high_spring():
    """Test classification of high spring tide."""
    phase = classify_tide_phase(5.0, is_high=True)
    assert phase == "spring"


def test_classify_tide_phase_high_neap():
    """Test classification of high neap tide."""
    phase = classify_tide_phase(3.0, is_high=True)
    assert phase == "neap"


def test_classify_tide_phase_high_medium():
    """Test classification of medium high tide."""
    phase = classify_tide_phase(4.0, is_high=True)
    assert phase == "medium"


def test_classify_tide_phase_low_spring():
    """Test classification of low spring tide."""
    phase = classify_tide_phase(0.5, is_high=False)
    assert phase == "spring"


def test_classify_tide_phase_low_neap():
    """Test classification of low neap tide."""
    phase = classify_tide_phase(2.5, is_high=False)
    assert phase == "neap"


def test_classify_tide_phase_low_medium():
    """Test classification of medium low tide."""
    phase = classify_tide_phase(1.5, is_high=False)
    assert phase == "medium"


def test_get_tide_predictions_invalid_location(mocker):
    """Test getting predictions for invalid location raises error."""
    from src.api.services import get_tide_predictions

    locations = [
        Location(
            id="test-001",
            name="Test Location",
            region="Test Region",
            latitude=50.0,
            longitude=-4.0,
        )
    ]

    start = datetime(2026, 8, 11, 0, 0, 0)
    end = datetime(2026, 8, 18, 23, 59, 59)

    with pytest.raises(ValueError, match="Location not found"):
        get_tide_predictions("invalid-id", start, end, locations)
