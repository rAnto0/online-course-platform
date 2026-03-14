import logging

from app.core.config import settings


def setup_logging():
    logger = logging.getLogger("app")

    if logger.handlers:
        return

    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | "
        f"{settings.SERVICE_NAME} | "
        "%(name)s | %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False
