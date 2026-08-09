import pytest

from src.context import PipelineContext


def test_defaults_are_none():
    context = PipelineContext()

    assert context.weather is None
    assert context.weather_call is None
    assert context.tides is None
    assert context.tides_call is None
    assert context.parquet_path is None
    assert context.tides_parquet_path is None


def test_with_values_returns_updated_copy():
    original = PipelineContext()
    weather = {"main": {"temp": 10.5}}

    updated = original.with_values(
        weather=weather,
        weather_call={"latitude": 45.0, "longitude": -73.0},
    )

    assert original.weather is None
    assert updated.weather == weather
    assert updated.weather_call == {"latitude": 45.0, "longitude": -73.0}


def test_with_values_rejects_unknown_field():
    context = PipelineContext()

    with pytest.raises(TypeError, match="unexpected keyword argument"):
        context.with_values(unknown="value")


def test_require_returns_present_field():
    context = PipelineContext(weather={"main": {"temp": 10.5}})

    assert context.require("weather") == {"main": {"temp": 10.5}}


def test_require_raises_for_missing_field():
    context = PipelineContext()

    with pytest.raises(KeyError, match="context is missing 'weather'"):
        context.require("weather")


def test_require_raises_for_unknown_field():
    context = PipelineContext()

    with pytest.raises(KeyError, match="unknown context field 'nope'"):
        context.require("nope")
