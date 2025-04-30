import hmac
from datetime import UTC, datetime
from hashlib import sha256

import httpx
import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src import core
from src.app import models

settings = core.config.get_settings()
pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture
def fake_telegram_data(
    telegram_id: int = 1337228,
    username: str = "brainrot_1337",
    first_name: str = "Lirali",
    last_name: str = "Larila",
    photo_url: str = "https://example.com/photo.jpg",
) -> dict:
    data = {
        "id": telegram_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "photo_url": photo_url,
        "auth_date": int(datetime.now(tz=UTC).timestamp()),
        "hash": "",  # Will be calculated
    }

    sorted_params = sorted(f"{x}={y}" for x, y in data.items() if x != "hash")
    data_check_bytes = "\n".join(sorted_params).encode()

    # Calculate HMAC
    computed_hash = hmac.new(settings.TG.BOT_SECRET, data_check_bytes, sha256).hexdigest()

    data["hash"] = computed_hash
    return data


async def test_auth_new_user(
    client: AsyncClient, fake_telegram_data: dict, db_session: AsyncSession
):
    response: httpx.Response = await client.post("/auth/login", json=fake_telegram_data)

    assert "detail" not in response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "session" in response.cookies

    # Check that user was created in the database
    user: models.User | None = await db_session.scalar(
        select(models.User).where(models.User.telegram_id == fake_telegram_data["id"])
    )

    assert user is not None
    assert user.telegram_username == fake_telegram_data["username"]

    # Check that organization was created in the database
    org: models.Organization | None = await db_session.scalar(
        select(models.Organization).where(
            models.Organization.name == fake_telegram_data["username"].capitalize()
        )
    )
    assert org is not None

    # Check that membership was created in the database with role CREATOR
    membership: models.Membership | None = await db_session.scalar(
        select(models.Membership)
        .where(models.Membership.user_id == user.id)
        .where(models.Membership.organization_id == org.id)
    )
    assert membership is not None
    assert membership.role == models.UserRoles.OWNER
