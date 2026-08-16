"""Tests for moon phase helper."""

from datetime import UTC, datetime

from src.weather.services.moon import moon_phase_fraction, moon_phase_name


def test_moon_phase_fraction_in_unit_interval() -> None:
    stamp = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)
    fraction = moon_phase_fraction(stamp)
    assert 0.0 <= fraction < 1.0


def test_moon_phase_name_is_non_empty() -> None:
    stamp = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)
    assert moon_phase_name(stamp)
