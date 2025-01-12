from uuid import UUID
from functools import lru_cache

from fastapi import Depends

from db.redis import redis_cache, redis_cache_list_and_page
from db.elastic import get_elastic
from db.abstract_storage import AbstractStorage
from models.genre import Genre
from services.abstract_service import AbstractService
from exceptions import NotDefinedMethod

GENRE_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class GenreService(AbstractService):
    def __init__(self, storage: AbstractStorage):
        self.storage = storage

    @redis_cache(Genre, GENRE_CACHE_EXPIRE_IN_SECONDS)
    async def get_by_id(self, genre_id: UUID) -> Genre | None:
        res = await self.storage.get_by_id(index="genres", query_id=genre_id)
        if res is None:
            return None
        return Genre(**res)

    @redis_cache_list_and_page(Genre, GENRE_CACHE_EXPIRE_IN_SECONDS)
    async def get_all(
        self,
        page_number: int,
        page_size: int,
    ) -> tuple[list[Genre], int]:
        res, number_of_pages = await self.storage.get_all(
            index="genres", page_number=page_number, page_size=page_size
        )
        if res is None or number_of_pages is None:
            return [], 0
        return [Genre(**item) for item in res], number_of_pages

    def search(self):
        raise NotDefinedMethod

    def __str__(self):
        # Reuired for the cache key
        return "GenreService"


@lru_cache()
def get_genre_service(
    storage: AbstractStorage = Depends(get_elastic),
) -> GenreService:
    return GenreService(storage)
