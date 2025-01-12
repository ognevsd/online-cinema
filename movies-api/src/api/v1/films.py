from uuid import UUID
from http import HTTPStatus
from typing import TypeVar, Generic

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from pydantic.generics import GenericModel

from services.film import get_film_service
from services.abstract_service import AbstractService
from services.auth_service import authorize, security_jwt

T = TypeVar("T")

router = APIRouter()


class PaginatedResponse(GenericModel, Generic[T]):
    page_number: int
    total_pages: int
    data: list[T]


class FilmworkGenreDetails(BaseModel):
    uuid: UUID
    name: str


class FilmworkPersonDetails(BaseModel):
    uuid: UUID
    name: str


class Film(BaseModel):
    uuid: UUID
    title: str
    imdb_rating: float | None
    description: str | None
    genre: list[FilmworkGenreDetails]
    actors: list[FilmworkPersonDetails]
    writers: list[FilmworkPersonDetails]
    directors: list[FilmworkPersonDetails]


@router.get(
    "/",
    summary="Все фильмы",
    description=(
        "Список всех фильмов, с пагинацией. Включает информацию об актерах, "
        "режиссерах, жанрах. Присутствует сортировка по рейтингу и "
        "фильтрация по жанру"
    ),
    response_model=PaginatedResponse[Film],
)
@authorize(roles=["superuser", "admin", "subscriber"])
async def all_films(
    sort: str = Query(
        "-imdb_rating",
        enum=["imdb_rating", "-imdb_rating"],
        description=(
            "Select imdb_rating for ascending sort and -imdb_rating for "
            "descending"
        ),
    ),
    page_number: int = Query(1, ge=1, le=1000),
    page_size: int = Query(100, ge=1, le=1000),
    genre_uuid: UUID | None = Query(
        None, description="Filter movies by genre id"
    ),
    authorization=Depends(security_jwt),
    film_service: AbstractService = Depends(get_film_service),
):
    films, total_pages = await film_service.get_all(
        page_number=page_number,
        page_size=page_size,
        sort=sort,
        genre_uuid=genre_uuid,
    )
    data = [Film(**film.model_dump()) for film in films]
    return PaginatedResponse(
        page_number=page_number, total_pages=total_pages, data=data
    )


@router.get(
    "/search",
    summary="Поиск фильмов",
    description="Полнотекстовый поиск по кинопроизведениям",
    response_model=PaginatedResponse[Film],
)
async def search_film(
    query: str,
    page_number: int = Query(1, ge=1, le=1000),
    page_size: int = Query(100, ge=1, le=1000),
    film_service: AbstractService = Depends(get_film_service),
):
    films, total_pages = await film_service.search(
        query, page_number, page_size
    )
    data = [Film(**film.model_dump()) for film in films]
    return PaginatedResponse(
        page_number=page_number, total_pages=total_pages, data=data
    )


@router.get(
    "/{film_id}",
    summary="Детальная информация о фильме",
    description="Детальная информация о фильме с указанным UUID",
    response_model=Film,
)
async def film_details(
    film_id: UUID,
    film_service: AbstractService = Depends(get_film_service),
) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Film not found"
        )
    return Film(**film.model_dump())
