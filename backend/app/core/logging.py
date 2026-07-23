"""Application-wide logging configuration."""

import logging

from app.config import settings


def configure_logging() -> None:
    """Configure root logging handlers and level once at startup."""
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
