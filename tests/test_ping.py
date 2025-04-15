import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_register_user_invalid_data(client: AsyncClient):
    user_data = {"name": "TestName1"}
    response = await client.post("/public/register", json=user_data)

    assert response.status_code == status.HTTP_200_OK

    response = await client.post("/public/register", json=user_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST  # unique constraint on user name
