import json
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from ...context import PipelineContext
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


@register_task("weather_forecast_parquet")
class WeatherForecastParquetTask(BaseTask):
    def __init__(self, params: dict):
        self.params = params

    def run(self, context: PipelineContext) -> PipelineContext:
        forecast = context.require("weather_forecast")
        forecast_call = context.require("weather_forecast_call")
        if not isinstance(forecast, dict) or not isinstance(forecast_call, dict):
            raise TypeError("weather_forecast and weather_forecast_call must be dicts")

        output_path = Path(self.params["output_path"])

        row = {
            "latitude": float(forecast_call["latitude"]),
            "longitude": float(forecast_call["longitude"]),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "response": json.dumps(forecast),
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        append_row(output_path, row)

        row_count = pq.read_table(output_path).num_rows
        logger.info("Wrote parquet row to %s (%d rows total)", output_path, row_count)

        return context.with_values(weather_forecast_parquet_path=str(output_path))
