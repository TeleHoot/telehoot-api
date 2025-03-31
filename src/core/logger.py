import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from src.core import config

settings = config.get_settings()

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

REPOSITORY_LOG_FILE = LOG_DIR / "repository.log"
SERVICE_LOG_FILE = LOG_DIR / "service.log"
API_LOG_FILE = LOG_DIR / "api.log"

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"  # noqa: Typo,


def setup_logger(name: str, log_file: Path, level: int = logging.INFO) -> logging.Logger:
    """Sets up a logger with a TimedRotatingFileHandler and optionally console output.

    Args:
        name (str): Name of the logger.
        log_file (Path): Path to the log file.
        level (int): Logging level.

    Returns:
        logging.Logger: Configured logger.

    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent logging from propagating to the root logger
    logger.propagate = False

    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if settings.DEBUG:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


repository_logger = setup_logger("repository", REPOSITORY_LOG_FILE)
service_logger = setup_logger("service", SERVICE_LOG_FILE)
api_logger = setup_logger("api", API_LOG_FILE)
