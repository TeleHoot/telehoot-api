from pathlib import Path

ENV_FILE_PATH: Path = Path(__file__).parents[3] / ".env"
if not ENV_FILE_PATH.exists():
    import logging

    logger = logging.getLogger(__name__)
    msg = f".env file not found at {ENV_FILE_PATH}. Using default settings."
    logger.critical(
        msg,
        stacklevel=2,
    )
