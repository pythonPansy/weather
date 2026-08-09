import json

import pyarrow.parquet as pq
import pytest

from src.context import PipelineContext
from src.tasks.export.tides_parquet import PARQUET_COLUMNS, TidesParquetTask
from tests.helpers import print_parquet_table


def _sample_context():
    return PipelineContext(
        tides_call={"latitude": 50.547, "longitude": -3.497},
        tides={
            "distance_km": 39.7,
            "place": {"name": "Salcombe", "latitude": 50.2368, "longitude": -3.773},
            "datum": "MSL",
            "unit": "m",
            "time_zone": "Europe/London",
            "source": "Predictions: Open-Meteo Marine",
            "extrema": [
                {
                    "time": "2026-08-09T08:00:00.000Z",
                    "date": "2026-08-09",
                    "height_m": 1.35,
                    "is_high": True,
                }
            ],
            "licence": "https://open-meteo.com/en/license",
        },
    )


def test_writes_row_to_new_parquet_file(tmp_path):
    output_path = tmp_path / "tides.parquet"
    task = TidesParquetTask(params={"output_path": str(output_path)})

    result = task.run(_sample_context())

    table = pq.read_table(output_path)
    print_parquet_table(table)
    assert table.num_rows == 1
    assert table.column_names == list(PARQUET_COLUMNS)
    assert table.column("latitude")[0].as_py() == 50.547
    assert table.column("longitude")[0].as_py() == -3.497
    response = json.loads(table.column("response")[0].as_py())
    assert response == _sample_context().tides
    assert "licence" in response
    assert "license" not in response
    assert result.tides_parquet_path == str(output_path)
    assert result.tides == _sample_context().tides


def test_appends_second_row(tmp_path):
    output_path = tmp_path / "tides.parquet"
    task = TidesParquetTask(params={"output_path": str(output_path)})

    task.run(_sample_context())
    task.run(
        PipelineContext(
            tides_call={"latitude": 50.37, "longitude": -4.14},
            tides={"place": {"name": "Plymouth"}, "extrema": []},
        )
    )

    table = pq.read_table(output_path)
    print_parquet_table(table)
    assert table.num_rows == 2
    assert table.column("latitude")[1].as_py() == 50.37
    assert (
        json.loads(table.column("response")[1].as_py())["place"]["name"] == "Plymouth"
    )


def test_raises_when_tides_missing(tmp_path):
    output_path = tmp_path / "tides.parquet"
    task = TidesParquetTask(params={"output_path": str(output_path)})

    with pytest.raises(KeyError, match="tides"):
        task.run(
            PipelineContext(
                tides_call={"latitude": 50.547, "longitude": -3.497},
            )
        )
