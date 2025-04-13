import logging
from pathlib import Path

ENV_FILE_PATH: Path = Path(__file__).parents[3] / ".env"
if not ENV_FILE_PATH.exists():
    logger = logging.getLogger(__name__)
    msg = f".env file not found at {ENV_FILE_PATH}. Using default settings."
    logger.warning(
        msg,
        stacklevel=2,
    )
