"""Entry point for the FIFI application."""

from __future__ import annotations

from .app import run_app
from .logging_utils import configure_logging


def main() -> None:
    configure_logging()
    run_app()


if __name__ == "__main__":
    main()
