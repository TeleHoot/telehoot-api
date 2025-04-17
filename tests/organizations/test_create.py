import httpx
import pytest
from fastapi import status

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_create_organizations_success(client: httpx.AsyncClient):
    org_data = {"name": "TestName"}
    response: httpx.Response = await client.post("/organizations/", json=org_data)

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()

    assert response_data.get("name") == org_data["name"]
    assert "id" in response_data


@pytest.mark.parametrize(
    ("test_name", "status_code"),
    [
        ("", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("W", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("WW", status.HTTP_201_CREATED),
    ],
)
async def test_create_organizations_length(
    test_name: str, status_code: int, client: httpx.AsyncClient
):
    org_data = {"name": test_name}
    response: httpx.Response = await client.post("/organizations/", json=org_data)

    assert response.status_code == status_code

    response_data = response.json()

    if response.is_success:
        assert response_data.get("name") == test_name
        assert "id" in response_data
    else:
        assert "detail" in response_data


async def test_read_organizations_empty_db(client: httpx.AsyncClient):
    response: httpx.Response = await client.get("/organizations/")

    assert response.json() == []


async def test_read_many_organizations(client: httpx.AsyncClient):
    num_created, org_data = 3, {"name": "TestName"}
    for _ in range(num_created):
        await client.post("/organizations/", json=org_data)

    response: httpx.Response = await client.get("/organizations/")

    assert response.status_code == status.HTTP_200_OK

    assert len(response.json()) == num_created
