from pathlib import Path

import pytest

from src.__main__ import main


def test_main_runs_runner_for_existing_config(tmp_path, mocker):
    config_path = tmp_path / "pipeline.yaml"
    config_path.write_text("tasks: []\n", encoding="utf-8")
    mock_runner = mocker.patch("src.__main__.TaskRunner")
    mock_runner.return_value.run.return_value = object()

    exit_code = main([str(config_path)])

    assert exit_code == 0
    mock_runner.assert_called_once_with(str(config_path))
    mock_runner.return_value.run.assert_called_once_with()


def test_main_returns_one_when_config_missing(tmp_path):
    missing = tmp_path / "missing.yaml"

    exit_code = main([str(missing)])

    assert exit_code == 1


def test_main_returns_one_when_runner_raises(tmp_path, mocker):
    config_path = tmp_path / "pipeline.yaml"
    config_path.write_text("tasks: []\n", encoding="utf-8")
    mock_runner = mocker.patch("src.__main__.TaskRunner")
    mock_runner.return_value.run.side_effect = RuntimeError("boom")

    exit_code = main([str(config_path)])

    assert exit_code == 1


def test_main_requires_config_path():
    with pytest.raises(SystemExit) as exc_info:
        main([])

    assert exc_info.value.code == 2


def test_main_accepts_path_object_string(tmp_path, mocker):
    config_path = Path(tmp_path / "pipeline.yaml")
    config_path.write_text("tasks: []\n", encoding="utf-8")
    mocker.patch("src.__main__.TaskRunner").return_value.run.return_value = object()

    assert main([str(config_path)]) == 0
