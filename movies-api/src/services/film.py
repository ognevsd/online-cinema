from uuid import UUID
from functools import lru_cache

from fastapi import Depends

from db.abstract_storage import AbstractStorage
from db.elastic import get_elastic
from db.redis import redis_cache, redis_cache_list_and_page
from models.film import Film
from services.abstract_service import AbstractService

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class FilmService(AbstractService):
    def __init__(self, storage: AbstractStorage):
        self.storage = storage

    @redis_cache(Film, FILM_CACHE_EXPIRE_IN_SECONDS)
    async def get_by_id(self, film_id: UUID) -> Film | None:
        res = await self.storage.get_by_id(index="movies", query_id=film_id)
        if res is None:
            return None
        return Film(**res)

    @redis_cache_list_and_page(Film, FILM_CACHE_EXPIRE_IN_SECONDS)
    async def get_all(
        self,
        page_number: int,
        page_size: int,
        sort: str | None,
        genre_uuid: UUID | None = None,
    ) -> tuple[list[Film], int]:

        if genre_uuid:
            genre_filter = {
                "nested": {
                    "path": "genre",
                    "query": {
                        "bool": {
                            "must": [{"term": {"genre.uuid": str(genre_uuid)}}]
                        }
                    },
                }
            }
        else:
            genre_filter = None

        res, number_of_pages = await self.storage.get_all(
            index="movies",
            page_number=page_number,
            page_size=page_size,
            sort=sort,
            filter=genre_filter,
        )

        if res is None or number_of_pages is None:
            return [], 0

        return [Film(**item) for item in res], number_of_pages

    @redis_cache_list_and_page(Film, FILM_CACHE_EXPIRE_IN_SECONDS)
    async def search(
        self,
        search_query: str,
        page_number: int,
        page_size: int,
    ) -> tuple[list[Film], int]:
        query = {
            "query": {
                "multi_match": {
                    "query": search_query,
                    "fields": [
                        "genre.name",
                        "directors.name",
                        "actors.name",
                        "writers.name",
                        "description",
                        "title",
                    ],
                }
            },
        }

        res, number_of_pages = await self.storage.search(
            index="movies",
            query=query,
            page_size=page_size,
            page_number=page_number,
        )

        if res is None or number_of_pages is None:
            return [], 0
        return [Film(**item) for item in res], number_of_pages

    def __str__(self):
        # Reuired for the cache key
        return "FilmService"


@lru_cache()
def get_film_service(
    storage: AbstractStorage = Depends(get_elastic),
) -> FilmService:
    return FilmService(storage)
