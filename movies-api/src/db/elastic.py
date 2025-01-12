import math

from uuid import UUID
from elasticsearch import AsyncElasticsearch, NotFoundError

from db.abstract_storage import AbstractStorage

es: AsyncElasticsearch | None = None


class ElasticStorage(AbstractStorage):
    async def get_by_id(self, index: str, query_id: UUID) -> dict | None:
        try:
            doc = await es.get(index=index, id=str(query_id))
        except NotFoundError:
            return None
        return doc["_source"]

    async def get_all(
        self,
        index: str,
        page_number: int,
        page_size: int,
        sort: str | None = None,
        filter: dict | None = None,
    ) -> tuple[list[dict], int] | tuple[None, None]:
        page_from = (page_number - 1) * page_size

        query = {
            "query": {"bool": {"must": [{"match_all": {}}]}},
            "size": page_size,
            "from": page_from,
        }

        if sort:
            sort_key = sort[1:] if sort[0] == "-" else sort
            sort_order = "desc" if sort[0] == "-" else "asc"
            query["sort"] = [{sort_key: sort_order}]

        if filter:
            query["query"]["bool"]["must"].append(filter)

        try:
            res = await es.search(index=index, body=query)
            number_of_pages = math.ceil(
                res["hits"]["total"]["value"] / page_size
            )
        except NotFoundError:
            return None, None
        return [
            item["_source"] for item in res["hits"]["hits"]
        ], number_of_pages

    async def search(
        self,
        index: str,
        query: dict,
        page_number: int,
        page_size: int,
    ) -> tuple[list[dict], int] | tuple[None, None]:
        query["sort"] = ["_score"]
        query["size"] = page_size
        query["from"] = (page_number - 1) * page_size

        try:
            res = await es.search(index=index, body=query)
            number_of_pages = math.ceil(
                res["hits"]["total"]["value"] / page_size
            )
        except NotFoundError:
            return None, None
        return [
            item["_source"] for item in res["hits"]["hits"]
        ], number_of_pages


# Функция понадобится при внедрении зависимостей
async def get_elastic() -> ElasticStorage:
    return ElasticStorage()
