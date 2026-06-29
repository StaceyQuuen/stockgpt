from loguru import logger
from app.core.config import settings
import sys


def setup_logger():

    logger.remove()

    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time}</green> | <level>{level}</level> | {message}"
    )

    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="7 days",
        level=settings.LOG_LEVEL
    )

    return logger


log = setup_logger()