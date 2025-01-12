import aiohttp
import pytest_asyncio

from functional.settings import test_settings


@pytest_asyncio.fixture(name="api_client_session", scope="session")
async def api_client_session():
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest_asyncio.fixture(name="make_get_request")
def make_get_request(api_client_session):
    async def inner(endpoint: str, query_data: dict):
        url = (
            f"http://{test_settings.api_host}:{test_settings.api_port}"
            f"/api/v1/{endpoint}"
        )
        async with api_client_session.get(url, params=query_data) as response:
            body = await response.json()
            headers = response.headers
            status = response.status
        return body, headers, status

    return inner
