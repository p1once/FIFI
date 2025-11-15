"""Utilities for structured logging throughout the application."""

from __future__ import annotations

import logging
import sys
from typing import Optional

from rich.logging import RichHandler


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the root logger with a Rich handler."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[RichHandler(rich_tracebacks=True, markup=True, show_path=False, console=None)],
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a module-level logger."""
    if not logging.getLogger().handlers:
        configure_logging()
    return logging.getLogger(name if name else __name__)


__all__ = ["configure_logging", "get_logger"]
