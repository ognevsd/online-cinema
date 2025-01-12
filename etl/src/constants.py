from enum import Enum
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_PATH = Path(__file__).parent.parent


class IndexNames(Enum):
    MOVIES = "movies"
    PERSONS = "persons"
    GENRES = "genres"


class Settings(BaseSettings):
    psql_db_name: str
    psql_user: str
    psql_password: str
    psql_host: str
    psql_port: str

    elasticsearch_host: str
    elasticsearch_port: str
    config_path: Path = ROOT_PATH / "src" / "config"

    elasticsearch_indices: dict[IndexNames, Path] = {
        IndexNames.MOVIES: config_path / "filmwork_index.json",
        IndexNames.PERSONS: config_path / "person_index.json",
        IndexNames.GENRES: config_path / "genre_index.json",
    }

    redis_host: str
    redis_port: str

    chunk_size: int = 200
    time_between_executions: int = 1  # sleep time after each execution in sec
    etl_sleep: int = 60  # sleep time after all data is updates in sec

    model_config = SettingsConfigDict(
        env_file=(".env"),
        env_file_encoding="utf-8",
    )


settings = Settings()
