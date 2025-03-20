import sys
import logging
import structlog

from typing import Any
from datetime import datetime

from bookstore.config import config


logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)


structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("Bookstore Logger")


def setup_logging():
    logger.info("Setting up logging")
    logger.info("Logging initialized", app=config.PROJECT_NAME)


def get_logger(module_name: str) -> structlog.BoundLogger:
    return structlog.get_logger(module_name)