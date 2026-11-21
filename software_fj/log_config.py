"""Log file configuration (events and errors).

This is the ONLY file the system writes to: there is no database.
"""

import logging
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "software_fj.log"
ROOT_LOGGER = "software_fj"


def configure_logger(log_file: Path = LOG_FILE) -> logging.Logger:
    """Configure the root system logger once and return it."""
    logger = logging.getLogger(ROOT_LOGGER)

    # Already configured: avoid duplicated handlers (and duplicated lines).
    if logger.handlers:
        return logger

    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handler: logging.Handler = logging.FileHandler(log_file, encoding="utf-8")
    except OSError as error:
        # If the file cannot be opened the app must NOT stop: fall back to stderr.
        handler = logging.StreamHandler()
        print(f"WARNING: cannot open log file ({error}); logging to console.")
    finally:
        # Always executed: set the minimum level regardless of the handler used.
        logger.setLevel(logging.INFO)

    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    return logger


def get_logger(module: str) -> logging.Logger:
    """Return a child logger, e.g. software_fj.reservation."""
    configure_logger()
    return logging.getLogger(f"{ROOT_LOGGER}.{module}")
