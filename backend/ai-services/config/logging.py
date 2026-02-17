import logging
import sys
from .settings import settings


def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("ai-services.log")
        ]
    )
    return logging.getLogger(settings.APP_NAME)


logger = setup_logging()
