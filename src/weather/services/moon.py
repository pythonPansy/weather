"""Astronomical moon-phase helper (no vendor required)."""

from __future__ import annotations

from datetime import UTC, datetime

# Synodic month length in days; reference is a known new moon (UTC).
_SYNODIC_DAYS = 29.530588853
_KNOWN_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=UTC)

_PHASE_NAMES = (
    (0.0625, "New moon"),
    (0.1875, "Waxing crescent"),
    (0.3125, "First quarter"),
    (0.4375, "Waxing gibbous"),
    (0.5625, "Full moon"),
    (0.6875, "Waning gibbous"),
    (0.8125, "Last quarter"),
    (0.9375, "Waning crescent"),
)


def moon_phase_fraction(moment: datetime) -> float:
    """Return illuminated-cycle fraction in [0, 1), where 0 is new moon."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    else:
        moment = moment.astimezone(UTC)
    days = (moment - _KNOWN_NEW_MOON).total_seconds() / 86_400.0
    return (days % _SYNODIC_DAYS) / _SYNODIC_DAYS


def moon_phase_name(moment: datetime) -> str:
    """Return a UK-English phase label for the given datetime."""
    fraction = moon_phase_fraction(moment)
    for boundary, name in _PHASE_NAMES:
        if fraction < boundary:
            return name
    return "New moon"
