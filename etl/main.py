import time
import datetime as dt

from loguru import logger
from pydantic import ValidationError
from src.constants import IndexNames, settings
from src.elastic_search_client import ElasticSearchClient
from src.exceptions import ElasticSearchClientException
from src.filmwork_etl import filmwork_etl
from src.genre_etl import genre_etl
from src.persons_etl import person_etl
from src.postgres_client import PostgresClient
from src.state_manager import RedisStateStorage


def main():
    dsl = {
        "dbname": settings.psql_db_name,
        "user": settings.psql_user,
        "password": settings.psql_password,
        "host": settings.psql_host,
        "port": settings.psql_port,
    }
    psql_client = PostgresClient(dsl)
    redis_storage = RedisStateStorage(settings.redis_host, settings.redis_port)
    es_client = ElasticSearchClient(
        settings.elasticsearch_host, settings.elasticsearch_port
    )
    default_date = dt.datetime.min

    with es_client as client:
        client.create_index(IndexNames.MOVIES)
        client.create_index(IndexNames.PERSONS)
        client.create_index(IndexNames.GENRES)

        while True:
            try:
                filmwork_etl(
                    es_client, redis_storage, psql_client, default_date
                )
                person_etl(es_client, redis_storage, psql_client, default_date)
                genre_etl(es_client, redis_storage, psql_client, default_date)
                time.sleep(settings.etl_sleep)

            except ValidationError as e:
                logger.error(f"Data validation failed: {e}")
                for error in e.errors():
                    loc = error.get("loc")
                    msg = error.get("msg")
                    error_type = error.get("type")
                    logger.error(
                        f"Field: {loc}, Error: {msg}, Type: {error_type}"
                    )
                raise
            except ElasticSearchClientException as e:
                logger.error(f"Failed bulk upload. {e}")
                raise
            except Exception as e:
                logger.error(f"Unknown exception occured: {e}")
                raise


if __name__ == "__main__":
    main()
