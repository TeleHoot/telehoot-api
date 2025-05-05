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
    response: httpx.Response = await client.post("/organizations/", json=data)
    response_data = response.json()

    if 200 <= status_code < 300:  # noqa: PLR2004
        assert "detail" not in response_data
    else:
        assert "detail" in response_data
        return None

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
    ],
)
async def test_create_organizations_length(
    test_name: str, status_code: int, user_client: httpx.AsyncClient
):
    org_data = {"name": test_name}
    await create_test_helper(data=org_data, status_code=status_code, client=user_client)


async def test_read_organizations_empty_db(client: httpx.AsyncClient):
    response: httpx.Response = await client.get("/organizations/")

    assert response.json() == []


async def test_read_many_organizations(user_client: httpx.AsyncClient, db_session: AsyncSession):
    num_created, org_data = 3, {"name": "TestName"}
    for _ in range(num_created):
        await user_client.post("/organizations/", json=org_data)

    response: httpx.Response = await user_client.get("/organizations/")

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
        f"/organizations/{org_id}/", json=update_org_data
    )

    response_data = response.json()

    assert "detail" not in response_data  # instead of status check

    assert response_data.get("name") == update_org_data["name"]
