"""Logging configuration helpers."""

import logging
import sys

from app.config.settings import Settings


def configure_logging(settings: Settings) -> None:
    """Configure root logging for CLI, API, and pipeline processes."""

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
