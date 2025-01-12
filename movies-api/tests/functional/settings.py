from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_host: str = Field("host.docker.internal")
    api_port: str = Field("8000")

    elastic_host: str = Field("host.docker.internal")
    elastic_port: int = Field("9200")
    elastic_schema: str = Field("http://")

    redis_host: str = Field("host.docker.internal")
    redis_port: int = Field("6379")

    test_data_path: Path = Path(__file__).parent / "testdata"

    @property
    def elastic_url(self):
        return f"{self.elastic_schema}{self.elastic_host}:{self.elastic_port}"


test_settings = TestSettings()
