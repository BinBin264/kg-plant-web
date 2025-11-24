import logging
import sys
from pathlib import Path

from .settings import settings

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "application.log"


def setup_logging() -> logging.Logger:
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()

    already_configured = any(
        isinstance(handler, logging.FileHandler)
        and getattr(handler, "baseFilename", None) == str(LOG_FILE)
        for handler in root_logger.handlers
    )
    if already_configured:
        root_logger.setLevel(log_level)
        return root_logger

    log_format = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(log_format)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(log_format)

    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
