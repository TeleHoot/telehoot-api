import hmac
from datetime import UTC, datetime
from hashlib import sha256
from httpx import AsyncClient

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src import core
from src.app import models

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

@pytest.mark.asyncio
async def test_auth_new_user_(client: AsyncClient, fake_telegram_data: dict, db_session: AsyncSession):
    response = await client.post("/auth", json=fake_telegram_data)

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

    # Check that user was created in the database
    user = await db_session.execute(select(models.User).where(models.User.telegram_id == fake_telegram_data["telegram_id"]))
    assert user.scalar_one_or_none() is not None
    assert user.scalar_one_or_none().telegram_username == fake_telegram_data["telegram_username"]

    # Check that organization was created in the database
    org = await db_session.execute(select(models.Organization).where(models.Organization.name == fake_telegram_data["telegram_username"].capitalize()))
    assert org.scalar_one_or_none() is not None

    # Check that organization_user was created in the database with role CREATOR
    org_user = await db_session.execute(select(models.OrganizationUser).where(models.OrganizationUser.user_id == user.scalar_one_or_none().id))
    assert org_user.scalar_one_or_none() is not None
    assert org_user.scalar_one_or_none().role == models.UserRoles.CREATOR
