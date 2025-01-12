from uuid import UUID
from functools import lru_cache

from fastapi import Depends

from db.elastic import get_elastic
from db.redis import redis_cache, redis_cache_list_and_page
from db.abstract_storage import AbstractStorage
from models.person import Person
from models.film import Film
from services.abstract_service import AbstractService
from exceptions import NotDefinedMethod

PERSON_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class PersonService(AbstractService):
    def __init__(self, storage: AbstractStorage):
        self.storage = storage

    @redis_cache(Person, PERSON_CACHE_EXPIRE_IN_SECONDS)
    async def get_by_id(self, person_id: UUID) -> Person | None:
        res = await self.storage.get_by_id(index="persons", query_id=person_id)
        if res is None:
            return None
        return Person(**res)

    @redis_cache_list_and_page(Person, PERSON_CACHE_EXPIRE_IN_SECONDS)
    async def search(
        self,
        search_query: str,
        page_number: int,
        page_size: int,
    ) -> tuple[list[Person], int]:
        query = {
            "query": {
                "multi_match": {
                    "query": search_query,
                    "fields": [
                        "full_name",
                    ],
                }
            },
        }

        res, number_of_pages = await self.storage.search(
            index="persons",
            query=query,
            page_number=page_number,
            page_size=page_size,
        )

        if res is None or number_of_pages is None:
            return [], 0
        return [Person(**item) for item in res], number_of_pages

    def get_all(self):
        raise NotDefinedMethod

    @redis_cache_list_and_page(Film, PERSON_CACHE_EXPIRE_IN_SECONDS)
    async def get_all_films(self, person_id: UUID) -> tuple[list[Film], int]:
        person_details = await self.get_by_id(person_id)
        if person_details is None:
            return [], 0

        ids_list = [str(item.uuid) for item in person_details.films]
        query = {"query": {"terms": {"uuid": ids_list}}}

        data, number_of_pages = await self.storage.search(
            index="movies", query=query, page_number=1, page_size=len(ids_list)
        )
        if data is None or number_of_pages is None:
            return [], 0

        return [Film(**item) for item in data], number_of_pages

    def __str__(self):
        # Reuired for the cache key
        return "PersonService"


@lru_cache()
def get_person_service(
    storage: AbstractStorage = Depends(get_elastic),
) -> PersonService:
    return PersonService(storage)
