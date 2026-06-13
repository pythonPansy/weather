import logging
import os
import sys

_DEFAULT_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

_configured = False


def setup_logging(level: str | int | None = None) -> None:
    """Configure root logging once. Level defaults to LOG_LEVEL env or INFO."""
    global _configured
    if _configured:
        return

    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO")
    if isinstance(level, str):
        level = _LOG_LEVELS.get(level.upper(), logging.INFO)

    logging.basicConfig(level=level, format=_DEFAULT_FORMAT, stream=sys.stderr)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
