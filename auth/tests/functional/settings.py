from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_host: str
    api_port: int

    project_name: str = Field(default="Auth API для онлайн-кинотеатра")
    project_version: str = Field(default="1.0.0")

    psql_host: str = Field()
    psql_port: int = Field()
    psql_db_name: str = Field()
    psql_user: str = Field()
    psql_password: str = Field()

    redis_host: str = Field()
    redis_port: int = Field()

    base_dir: Path = Path(__file__).parent.parent

    jwt_secret: str = Field()
    token_expire: int = Field(default=15, description="Token expire time in minutes")
    refresh_expire: int = Field(
        default=14000, description="Refresh token expire in minutes"
    )
    algorithm: str = Field(default="HS256", description="Encryption algorithm for jwt")


settings = Settings()
