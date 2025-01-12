from enum import Enum
from pydantic import BaseModel, ConfigDict


class OAuthProviders(Enum):
    GOOGLE = "google"


class OAuthUserDetails(BaseModel):
    model_config = ConfigDict(extra="ignore")
    sub: str
    name: str
    given_name: str
    family_name: str
    email: str
    oauth_provider: OAuthProviders


class TokenPayload(BaseModel):
    login: str
    roles: list[str]
