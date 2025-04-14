import uuid
from datetime import UTC, datetime


class Base:
    key: str = f"{datetime.now(tz=UTC).strftime('%Y/%m/%d')}/{uuid.uuid4()}"
    content_type: str | None = None
