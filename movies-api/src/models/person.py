from uuid import UUID
from pydantic import BaseModel, ConfigDict


class PersonFilmDetails(BaseModel):
    uuid: UUID
    roles: list[str]


class Person(BaseModel):
    model_config = ConfigDict(extra="ignore")

    uuid: UUID
    full_name: str
    films: list[PersonFilmDetails]
