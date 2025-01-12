from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    login: str
    password: str
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)


class UserUpdate(BaseModel):
    login: str | None = Field(default=None)
    password: str | None = Field(default=None)
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)


class UserInDB(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    id: UUID
    login: str
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    roles: list[str] = Field(default=[])


class UserLogin(BaseModel):
    login: str
    password: str
