from uuid import UUID
from http import HTTPStatus
from typing import TypeVar, Generic

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from pydantic.generics import GenericModel

from services.person import get_person_service, PersonService
from services.abstract_service import AbstractService


T = TypeVar("T")

router = APIRouter()


class PaginatedResponse(GenericModel, Generic[T]):
    page_number: int
    total_pages: int
    data: list[T]


class PersonFilmDetails(BaseModel):
    uuid: UUID
    roles: list[str]


class Person(BaseModel):
    uuid: UUID
    full_name: str
    films: list[PersonFilmDetails]


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
    "/search",
    summary="Поиск человека",
    description="Полнотекстовый поиск по людям",
    response_model=PaginatedResponse[Person],
)
async def search_person(
    query: str,
    page_number: int = Query(1, ge=1, le=1000),
    page_size: int = Query(100, ge=1, le=1000),
    person_service: AbstractService = Depends(get_person_service),
):
    persons, total_pages = await person_service.search(
        query, page_number, page_size
    )
    data = [Person(**person.model_dump()) for person in persons]
    return PaginatedResponse(
        page_number=page_number, total_pages=total_pages, data=data
    )


@router.get(
    "/{person_id}",
    summary="Детальная информация о человеке",
    description="Детальная информация о человеке с указанным UUID",
    response_model=Person,
)
async def person_details(
    person_id: UUID,
    person_service: AbstractService = Depends(get_person_service),
):
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Person not found"
        )
    return Person(**person.model_dump())


@router.get(
    "/{person_id}/film",
    summary="Список фильмов",
    description="Детальная информация о фильмах, связанных с человеком с "
    "указанным UUID",
    response_model=list[Film],
)
async def person_films(
    person_id: UUID,
    person_service: PersonService = Depends(get_person_service),
):
    film_details, _ = await person_service.get_all_films(person_id)
    if not film_details or len(film_details) == 0:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Person not found"
        )

    return [
        Film(**film.model_dump()) for film in film_details if film is not None
    ]
