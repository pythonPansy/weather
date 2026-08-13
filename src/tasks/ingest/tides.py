"""Tide ingestion task for the YAML task runner."""

import sys
from pathlib import Path

# Allow imports from project root when run as a standalone task module.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.tasks.base import BaseTask  # noqa: E402
from src.tasks.registry import register_task  # noqa: E402
from src.weather.services.ingest import run_tide_ingest_sync  # noqa: E402


@register_task("tide_ingest")
class TideIngestTask(BaseTask):
    def __init__(self, params: dict):
        self.params = params

    def run(self, context: dict) -> dict:
        count = run_tide_ingest_sync()
        context["tides_ingested"] = count
        return context
