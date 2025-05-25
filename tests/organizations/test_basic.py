from typing import Any

import httpx
import pytest
from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app import models

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def create_test_helper(
    *,
    data: dict[str, Any],
    status_code: int,
    client: httpx.AsyncClient,
    session: AsyncSession | None = None,
) -> str | None:
    response: httpx.Response = await client.post("/organizations", json=data)
    response_data = response.json()

    if status_code >= status.HTTP_400_BAD_REQUEST:
        assert "detail" in response_data
        return None
    assert "detail" not in response_data

    assert response.status_code == status_code

    for given_field, given_value in data.items():
        assert response_data.get(given_field) == given_value
    assert "id" in response_data
    org_id: str = response_data["id"]
    if session:
        organization = await session.get(models.Organization, org_id)

        assert organization is not None

        for given_field, given_value in data.items():
            assert getattr(organization, given_field) == given_value
    return org_id


async def test_create_organizations_success(
    user_client: httpx.AsyncClient, db_session: AsyncSession
):
    org_data = {"name": "Tralalello Tralala"}
    await create_test_helper(
        data=org_data, status_code=status.HTTP_201_CREATED, client=user_client, session=db_session
    )


@pytest.mark.parametrize(
    ("test_name", "status_code"),
    [
        ("", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("W", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("WW", status.HTTP_201_CREATED),
        ("          ", status.HTTP_422_UNPROCESSABLE_ENTITY),
    ],
)
async def test_create_organizations_length(
    test_name: str, status_code: int, user_client: httpx.AsyncClient
):
    org_data = {"name": test_name}
    await create_test_helper(data=org_data, status_code=status_code, client=user_client)


async def test_read_organizations_empty_db(client: httpx.AsyncClient):
    response: httpx.Response = await client.get("/organizations")

    assert response.json() == []


async def test_read_many_organizations(user_client: httpx.AsyncClient, db_session: AsyncSession):
    num_created, org_data = 3, {"name": "TestName"}
    for _ in range(num_created):
        await user_client.post("/organizations", json=org_data)

    response: httpx.Response = await user_client.get("/organizations")

    assert response.status_code == status.HTTP_200_OK

    assert len(response.json()) == num_created

    result = await db_session.scalars(select(models.Organization))
    assert len(result.all()) == num_created


async def test_update_organizations_success(
    user_client: httpx.AsyncClient, db_session: AsyncSession
):
    org_data = {"name": "Tralalello Tralala"}
    org_id = await create_test_helper(
        data=org_data, status_code=status.HTTP_201_CREATED, client=user_client, session=db_session
    )

    update_org_data = {"name": "Trippi Troppa"}
    response: httpx.Response = await user_client.patch(
        f"/organizations/{org_id}", json=update_org_data
    )

    response_data = response.json()

    assert "detail" not in response_data  # instead of status check

    assert response_data.get("name") == update_org_data["name"]


async def test_delete_organization(
    user_client: httpx.AsyncClient, membership_owner: models.Membership, db_session: AsyncSession
):
    response: httpx.Response = await user_client.delete(
        f"/organizations/{membership_owner.organization_id}"
    )
    assert response.json() == {"is_success": True}
    assert response.status_code == status.HTTP_200_OK

    org = await db_session.scalar(select(models.Organization))

    assert org is not None
    assert hasattr(org, "deleted_at")
    assert org.deleted_at is not None

    membership = await db_session.scalar(select(models.Membership))

    # check cascade delete
    assert membership is not None
    assert hasattr(membership, "deleted_at")
    assert membership.deleted_at is not None

    assert org.deleted_at == membership.deleted_at

    # deleted organization is not visible
    response: httpx.Response = await user_client.get("/organizations")

    assert response.json() == []


async def test_admin_sees_deleted_organizations(
    admin_client: httpx.AsyncClient, organization: models.Organization, db_session: AsyncSession
):
    await admin_client.delete(f"/organizations/{organization.id}")

    response = await admin_client.get("/organizations")
    response_data = response.json()
    assert len(response_data) == 1

    org = response_data[0]

    assert org.get("name") == organization.name
    assert org.get("id") == str(organization.id)


async def test_delete_organization_editor(
    user_client: httpx.AsyncClient, membership_editor: models.Membership, db_session: AsyncSession
):
    response: httpx.Response = await user_client.delete(
        f"/organizations/{membership_editor.organization_id}"
    )
    response_data = response.json()
    assert "detail" in response_data
    assert response_data.get("error_code") == "forbidden_access"
    assert response.status_code == status.HTTP_403_FORBIDDEN
