from uuid import UUID
from pydantic import BaseModel, ConfigDict


class Genre(BaseModel):
    model_config = ConfigDict(extra="ignore")

    uuid: UUID
    name: str
    description: str | None
