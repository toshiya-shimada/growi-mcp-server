from __future__ import annotations

import logging
import sys


def configure_logging(level: str) -> None:
    """Route all logs to stderr so stdio transport stays clean."""

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stderr,
        force=True,
    )
