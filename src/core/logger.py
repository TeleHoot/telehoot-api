import json
import sys
from datetime import UTC, datetime
from logging import Formatter, LogRecord
from pathlib import Path
from typing import ClassVar

from src.core import config

settings = config.get_settings()


class CustomConsoleFormatter(Formatter):
    COLORS: ClassVar = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[31;1m",  # Bold Red
        "RESET": "\033[0m",  # Reset
        "TIMESTAMP": "\033[90m",  # Gray
        "NAME": "\033[35m",  # Magenta
    }

    standard_attrs = frozenset({
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    })

    def format(self, record: LogRecord) -> str:
        level_color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        timestamp = f"{self.COLORS['TIMESTAMP']}[{self.formatTime(record, self.datefmt)}]{self.COLORS['RESET']}"  # noqa: E501
        level = f"{level_color}[{record.levelname}]{self.COLORS['RESET']}"
        name = f"{self.COLORS['NAME']}[{record.name}]{self.COLORS['RESET']}"
        message = f"{record.getMessage()}"

        formatted_message = f"{timestamp} {level} {name} {message}"

        extra_attrs = {k: v for k, v in record.__dict__.items() if k not in self.standard_attrs}
        if extra_attrs:
            formatted_message += f" {json.dumps(extra_attrs, default=str)}"

        if record.exc_info:
            formatted_message += f"\n{self.formatException(record.exc_info)}"

        return formatted_message


def setup_logger() -> dict:
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{datetime.now(UTC).strftime('%Y-%m-%d')}.log"

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "pythonjsonlogger.json.JsonFormatter",
                "format": settings.LOGGER.FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "uvicorn_access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(asctime)s [%(process)s] [%(levelname)s] [%(name)s] %(client_addr)s - "%(request_line)s" %(status_code)s',  # noqa: E501
            },
            "console": {
                "()": CustomConsoleFormatter,
                "format": "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "console",
                "level": "DEBUG",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "formatter": "default",
                "filename": str(log_file),
                "when": "midnight",
                "backupCount": settings.LOGGER.BACKUP_COUNT,
                "encoding": "utf-8",
                "utc": True,
            },
            "access_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "uvicorn_access",
                "filename": settings.LOGGER.ACCESS_LOG,
                "maxBytes": settings.LOGGER.MAX_BYTES,
                "backupCount": settings.LOGGER.BACKUP_COUNT,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": settings.LOGGER.LEVEL,
                "propagate": False,
            },
            "uvicorn.access": {"handlers": ["access_file"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"level": "INFO", "propagate": False},
            "sqlalchemy": {
                "level": "WARNING",
                "propagate": False,
                "handlers": ["console", "file"],
            },
            "sqlalchemy.engine": {
                "level": "INFO",
                "propagate": False,
                "handlers": ["console", "file"],
            },
            "pymongo": {"level": "WARNING", "propagate": False, "handlers": ["console", "file"]},
            "botocore": {"level": "WARNING", "propagate": False, "handlers": ["console", "file"]},
        },
    }
