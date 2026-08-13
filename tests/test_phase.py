"""Tests for spring/neap/medium tide phase classification."""

from decimal import Decimal

from src.weather.services.phase import classify_high_tide_phase


def test_classify_spring_above_mhws() -> None:
    result = classify_high_tide_phase(Decimal("5.0"), Decimal("4.8"), Decimal("3.5"))
    assert result == "spring"


def test_classify_neap_below_mhwn() -> None:
    result = classify_high_tide_phase(Decimal("3.0"), Decimal("4.8"), Decimal("3.5"))
    assert result == "neap"


def test_classify_medium_between_thresholds() -> None:
    result = classify_high_tide_phase(Decimal("4.0"), Decimal("4.8"), Decimal("3.5"))
    assert result == "medium"
