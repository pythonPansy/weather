import json
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from ...logging_config import get_logger
from ..base import BaseTask
from ..registry import register_task

logger = get_logger(__name__)

PARQUET_COLUMNS = ("latitude", "longitude", "fetched_at", "response")


def append_row(output_path: Path, row: dict) -> None:
    table = pa.Table.from_pylist([row])
    if output_path.exists():
        existing = pq.read_table(output_path)
        table = pa.concat_tables([existing, table])
    pq.write_table(table, output_path)


@register_task("weather_parquet")
class WeatherParquetTask(BaseTask):
    def __init__(self, params: dict):
        self.params = params

    def run(self, context: dict) -> dict:
        if "weather" not in context:
            raise KeyError("context is missing 'weather'; run weather_api first")
        if "weather_call" not in context:
            raise KeyError("context is missing 'weather_call'; run weather_api first")

        output_path = Path(self.params["output_path"])
        weather_call = context["weather_call"]

        row = {
            "latitude": float(weather_call["latitude"]),
            "longitude": float(weather_call["longitude"]),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "response": json.dumps(context["weather"]),
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        append_row(output_path, row)

        row_count = pq.read_table(output_path).num_rows
        logger.info("Wrote parquet row to %s (%d rows total)", output_path, row_count)

        context["parquet_path"] = str(output_path)
        return context
