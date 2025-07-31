import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.app import models

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_create_membership_success(
    user_client: httpx.AsyncClient,
    db_session: AsyncSession,
    user: models.User,
    organization: models.Organization,
):
    membership_data = {
        "organization_id": str(organization.id),
        "user_id": str(user.id),
        "role": models.UserRoles.OWNER,
        "status": models.MembershipStatuses.APPROVED,
    }
    response: httpx.Response = await user_client.post("/memberships", json=membership_data)

    response_data = response.json()
    assert "detail" not in response_data

    assert "organization" in response_data
    assert "user" in response_data
    assert response_data["user"]["id"] == membership_data["user_id"]
    assert response_data["organization"]["id"] == membership_data["organization_id"]

    assert response_data.get("role") == membership_data["role"]
    assert response_data.get("status") == membership_data["status"]
