import json
import pytest_asyncio

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from functional.settings import test_settings


@pytest_asyncio.fixture(name="es_client", scope="session")
async def es_client():
    es_client = AsyncElasticsearch(
        hosts=test_settings.elastic_url, verify_certs=False
    )
    yield es_client
    await es_client.close()


@pytest_asyncio.fixture(name="es_write_data")
def es_write_data(es_client):
    async def inner(data: list[dict], index_name: str, index_filename: str):
        if await es_client.indices.exists(index=index_name):
            await es_client.indices.delete(index=index_name)

        # Read index settings
        with open(test_settings.test_data_path / index_filename, "r") as file:
            es_index_mapping = json.load(file)

        await es_client.indices.create(index=index_name, **es_index_mapping)

        _, errors = await async_bulk(
            client=es_client, actions=data, refresh="wait_for"
        )

        if errors:
            raise Exception("Ошибка записи данных в Elasticsearch")

    return inner
