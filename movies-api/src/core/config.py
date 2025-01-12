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

    project_name: str = Field(default="Read-only API для онлайн-кинотеатра")
    project_description: str = Field(
        default="Информация о фильмах, жанрах и людях, участвовавших в "
        "создании произведения"
    )
    project_version: str = Field(default="1.0.0")

    elastic_host: str = Field()
    elastic_port: int = Field()
    elastic_schema: str = Field("http://")

    redis_host: str = Field()
    redis_port: int = Field()

    auth_service_host: str = Field()
    auth_service_port: int = Field(default=80)

    jaeger_host: str = Field()
    jaeger_port: int = Field(default=4318)

    base_dir: Path = Path(__file__).parent.parent

    debug: bool = Field(default=False)

    request_limit_per_minute: int = Field(default=10)

    @property
    def elastic_url(self):
        return f"{self.elastic_schema}{self.elastic_host}:{self.elastic_port}"


settings = Settings()
