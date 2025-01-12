from uuid import UUID
from pydantic import BaseModel, ConfigDict


class FilmworkGenreDetails(BaseModel):
    uuid: UUID
    name: str


class FilmworkPersonDetails(BaseModel):
    uuid: UUID
    name: str


class Film(BaseModel):
    model_config = ConfigDict(extra="ignore")

    uuid: UUID
    title: str
    imdb_rating: float | None
    description: str | None
    genre: list[FilmworkGenreDetails]
    actors: list[FilmworkPersonDetails]
    writers: list[FilmworkPersonDetails]
    directors: list[FilmworkPersonDetails]
