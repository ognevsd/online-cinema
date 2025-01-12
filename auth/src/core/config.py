from pathlib import Path
from logging import config as logging_config

from core.logger import LOGGING
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logging_config.dictConfig(LOGGING)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    debug: bool = Field(default=False)

    project_name: str = Field(default="Auth API для онлайн-кинотеатра")
    project_version: str = Field(default="1.0.0")

    psql_host: str = Field()
    psql_port: int = Field()
    psql_db_name: str = Field()
    psql_user: str = Field()
    psql_password: str = Field()

    redis_host: str = Field()
    redis_port: int = Field()

    jaeger_host: str = Field()
    jaeger_port: int = Field(default=4318)

    base_dir: Path = Path(__file__).parent.parent

    jwt_secret: str = Field()
    token_expire: int = Field(
        default=15, description="Token expire time in minutes"
    )
    refresh_expire: int = Field(
        default=14000, description="Refresh token expire in minutes"
    )
    algorithm: str = Field(
        default="HS256", description="Encryption algorithm for jwt"
    )

    # Google OAuth parameters
    google_client_config_path: Path = (
        Path(__file__).parent / "client_secret.json"
    )
    google_client_id: str = Field()
    google_oauth_scopes: list[str] = Field()
    oauth_redirect_uri: str = (
        "http://localhost:8000/api/v1/users/oauth2callback"
    )

    session_middleware_key: str = Field()


settings = Settings()
