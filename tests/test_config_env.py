import pytest

from src.config_env import expand_env_vars


def test_expands_whole_string_placeholder(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "secret-key")

    result = expand_env_vars({"api_key": "${OPENWEATHER_API_KEY}", "latitude": 45.0})

    assert result == {"api_key": "secret-key", "latitude": 45.0}


def test_expands_nested_dict_and_list(monkeypatch):
    monkeypatch.setenv("TOKEN", "abc")

    result = expand_env_vars(
        {
            "outer": {"token": "${TOKEN}"},
            "items": ["plain", "${TOKEN}", 1],
        }
    )

    assert result == {
        "outer": {"token": "abc"},
        "items": ["plain", "abc", 1],
    }


def test_passthrough_non_placeholder_strings():
    result = expand_env_vars({"path": "data/weather.parquet", "note": "prefix-${X}"})

    assert result == {"path": "data/weather.parquet", "note": "prefix-${X}"}


def test_missing_env_var_raises(monkeypatch):
    monkeypatch.delenv("MISSING_KEY", raising=False)

    with pytest.raises(ValueError, match="MISSING_KEY"):
        expand_env_vars({"api_key": "${MISSING_KEY}"})


def test_empty_env_var_raises(monkeypatch):
    monkeypatch.setenv("EMPTY_KEY", "")

    with pytest.raises(ValueError, match="EMPTY_KEY"):
        expand_env_vars({"api_key": "${EMPTY_KEY}"})
