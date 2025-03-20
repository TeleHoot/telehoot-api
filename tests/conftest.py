import pytest
from httpx import ASGITransport, AsyncClient

from src.config import get_settings
from src.main import app

pytest_plugins = ["pytest_asyncio"]

settings = get_settings()


@pytest.fixture(scope="session")
async def client():
    """Provide an AsyncClient."""
    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://test/api/v1"
    ) as client:
        yield client
