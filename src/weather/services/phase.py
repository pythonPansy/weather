"""Tide phase classification for spring, neap, and medium tides."""

from decimal import Decimal


def classify_high_tide_phase(
    height_metres: Decimal | float,
    mhws: Decimal | float,
    mhwn: Decimal | float,
) -> str:
    """Classify a high tide using MHWS/MHWN thresholds."""
    height = float(height_metres)
    springs = float(mhws)
    neaps = float(mhwn)

    if height > springs:
        return "spring"
    if height < neaps:
        return "neap"
    return "medium"


def classify_low_tide_phase(high_phase: str | None) -> str | None:
    """Low tides inherit the phase of the surrounding tidal cycle."""
    return high_phase
