from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .logging_config import get_logger
from .runner import TaskRunner

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src",
        description="Run the config-driven weather/tides task pipeline.",
    )
    parser.add_argument(
        "config_path",
        type=Path,
        help="Path to the YAML pipeline config (e.g. config/pipeline.yaml)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config_path = args.config_path

    if not config_path.is_file():
        logger.error("Config file not found: %s", config_path)
        return 1

    logger.info("Starting pipeline with config %s", config_path)
    try:
        TaskRunner(str(config_path)).run()
    except Exception:
        logger.exception("Pipeline failed")
        return 1

    logger.info("Pipeline finished successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
