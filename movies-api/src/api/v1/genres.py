from uuid import UUID
from http import HTTPStatus
from typing import TypeVar, Generic

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from pydantic.generics import GenericModel

from services.genre import get_genre_service
from services.abstract_service import AbstractService

T = TypeVar("T")

router = APIRouter()


class PaginatedResponse(GenericModel, Generic[T]):
    page_number: int
    total_pages: int
    data: list[T]


class Genre(BaseModel):
    uuid: UUID
    name: str
    description: str | None


@router.get(
    "/",
    summary="Все жанры",
    description=("Список всех жанров, с пагинацией"),
    response_model=PaginatedResponse[Genre],
)
async def all_genres(
    page_number: int = Query(1, ge=1, le=1000),
    page_size: int = Query(100, ge=1, le=1000),
    genre_service: AbstractService = Depends(get_genre_service),
):
    genres, total_pages = await genre_service.get_all(page_number, page_size)
    data = [
        Genre(uuid=genre.uuid, name=genre.name, description=genre.description)
        for genre in genres
    ]
    return PaginatedResponse(
        page_number=page_number, total_pages=total_pages, data=data
    )


@router.get(
    "/{genre_id}",
    summary="Детальная информация о жанре",
    description="Детальная информация о жанре с указанным UUID",
    response_model=Genre,
)
async def genre_details(
    genre_id: UUID, genre_service: AbstractService = Depends(get_genre_service)
):
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Genre not found"
        )
    return Genre(
        uuid=genre.uuid, name=genre.name, description=genre.description
    )
