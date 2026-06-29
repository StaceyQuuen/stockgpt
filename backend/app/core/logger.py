from loguru import logger
from app.core.config import settings
from app.core.trace import get_trace_id
import sys


def setup_logger():

    logger.remove()

    logger.add(
        sys.stdout,
        format="<green>{time}</green> | <level>{level}</level> | {extra[trace_id]} | {message}",
        level=settings.LOG_LEVEL,
    )

    return logger


log = setup_logger()


def log_with_trace(message: str):

    trace_id = get_trace_id()

    log.bind(trace_id=trace_id).info(message)