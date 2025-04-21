import hmac
from datetime import UTC, datetime
from hashlib import sha256

import pytest

from src import core

settings = core.config.get_settings()


@pytest.fixture
def fake_telegram_data(
    telegram_id: int = 12345,
    username: str = "test_user",
    first_name: str = "Test",
    last_name: str = "User",
    photo_url: str = "https://example.com/photo.jpg",
) -> dict:
    # Create base data without hash
    data = {
        "telegram_id": telegram_id,
        "username": username,
        "telegram_username": username,
        "first_name": first_name,
        "last_name": last_name,
        "photo_url": photo_url,
        "auth_date": int(datetime.now(tz=UTC).timestamp()),
        "hash": "",  # Will be calculated
    }

    # Create data check string
    data_check = []
    for key, value in data.items():
        if key != "hash" and value is not None:
            data_check.append(f"{key}={value}")

    data_check_string = "\n".join(sorted(data_check))

    # Calculate HMAC
    secret_key = sha256(settings.TG.BOT_SECRET.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), sha256).hexdigest()

    data["hash"] = computed_hash
    return data
