import datetime as dt
import uuid
from typing import Optional

from pydantic import BaseModel


class UuidTimestampMixin(BaseModel):
    uuid: uuid.UUID
    modified: dt.datetime


class Person(UuidTimestampMixin):
    pass


class Filmwork(UuidTimestampMixin):
    pass


class Genre(UuidTimestampMixin):
    name: str
    description: Optional[str]


class FullFilmworkInfo(UuidTimestampMixin):
    title: str
    description: Optional[str]
    rating: Optional[float]
    type: str
    created: dt.datetime
    role: Optional[str]
    person_id: Optional[uuid.UUID]
    full_name: Optional[str]
    genre_id: uuid.UUID
    genre_name: str


class FullPersonInfo(UuidTimestampMixin):
    full_name: str
    filmwork_id: uuid.UUID
    role: str
