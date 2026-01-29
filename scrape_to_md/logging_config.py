"""Logging configuration for scrape_to_md."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(name: str, log_file: Path) -> logging.Logger:
    """Setup logging with file and console handlers.

    Args:
        name: Logger name (typically __name__)
        log_file: Path to log file

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # File handler - DEBUG level with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Console handler - INFO level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
