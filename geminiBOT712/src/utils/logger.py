# src/utils/logger.py
# Standardized logger configuration for the entire application.

import logging
import sys
from config.settings import LOG_LEVEL, LOG_FORMAT

def get_logger(name: str) -> logging.Logger:
    """
    Creates and configures a logger instance.

    Args:
        name (str): The name for the logger, typically __name__.

    Returns:
        logging.Logger: A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    # Avoid adding duplicate handlers if already configured
    if not logger.handlers:
        # Console Handler
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(stream_handler)

        # File Handler
        file_handler = logging.FileHandler("trading_system.log")
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)

    return logger
