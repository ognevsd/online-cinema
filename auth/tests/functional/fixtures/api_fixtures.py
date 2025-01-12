import aiohttp
import pytest_asyncio

from functional.settings import settings


@pytest_asyncio.fixture(name="api_client_session", scope="session")
async def api_client_session():
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest_asyncio.fixture(name="make_get_request")
def make_get_request(api_client_session):
    async def inner(endpoint: str, headers: dict | None = None):
        url = (
            f"http://{settings.api_host}:{settings.api_port}/api/v1/{endpoint}"
        )
        async with api_client_session.get(url, headers=headers) as response:
            body = await response.json()
            headers = response.headers
            status = response.status
        return body, headers, status

    return inner


@pytest_asyncio.fixture(name="make_post_request")
def make_post_request(api_client_session):
    async def inner(
        endpoint: str,
        headers: dict | None = None,
        json: dict | None = None,
        data: dict | None = None,
    ):
        url = (
            f"http://{settings.api_host}:{settings.api_port}/api/v1/{endpoint}"
        )
        async with api_client_session.post(
            url, json=json, data=data, headers=headers
        ) as response:
            body = await response.json()
            headers = response.headers
            status = response.status
        return body, headers, status

    return inner


@pytest_asyncio.fixture(name="make_patch_request")
def make_patch_request(api_client_session):
    async def inner(
        endpoint: str,
        headers: dict | None = None,
        json: dict | None = None,
        data: dict | None = None,
    ):
        url = (
            f"http://{settings.api_host}:{settings.api_port}/api/v1/{endpoint}"
        )
        async with api_client_session.patch(
            url, json=json, data=data, headers=headers
        ) as response:
            body = await response.json()
            headers = response.headers
            status = response.status
        return body, headers, status

    return inner
