from src.core import config

settings = config.get_settings()


def setup_logger() -> dict:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": settings.LOGGER.FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "uvicorn_access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(asctime)s [%(process)s] [%(levelname)s] [%(name)s] %(client_addr)s - "%(request_line)s" %(status_code)s',  # noqa: E501
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "DEBUG",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "default",
                "filename": settings.LOGGER.FILE_PATH,
                "maxBytes": settings.LOGGER.MAX_BYTES,
                "backupCount": settings.LOGGER.BACKUP_COUNT,
            },
            "access_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "uvicorn_access",
                "filename": settings.LOGGER.ACCESS_LOG,
                "maxBytes": settings.LOGGER.MAX_BYTES,
                "backupCount": settings.LOGGER.BACKUP_COUNT,
            },
        },
        "loggers": {
            "": {"handlers": ["console", "file"], "level": settings.LOGGER.LEVEL},
            "uvicorn.access": {"handlers": ["access_file"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"level": "INFO", "propagate": True},
            "sqlalchemy": {"level": "WARNING", "propagate": True},
        },
    }
