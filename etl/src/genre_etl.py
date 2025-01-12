import datetime as dt
import time

from loguru import logger
from src.constants import settings
from src.data_description import Genre
from src.data_transformer import GenreTransformer
from src.elastic_search_client import ElasticSearchClient
from src.postgres_client import PostgresClient
from src.state_manager import RedisStateStorage, State


def _get_latest_state(
    storage: RedisStateStorage, default_date: dt.datetime
) -> dt.datetime:
    with storage:
        last_modified_genre = State(storage).get_state("genre_last_modified_genre")
        logger.info(f"Last modified genre: {last_modified_genre}")

    if last_modified_genre is None:
        last_modified_genre = default_date

    return last_modified_genre


def _get_person_data(
    client: PostgresClient,
    last_modified_genre: dt.datetime,
) -> tuple[list[Genre], dt.datetime]:
    with client:
        modified_genres = client.query_genres(last_modified_genre)

        logger.info(f"Queried: {len(modified_genres)} genres")
        if len(modified_genres) == 0:
            logger.info("No recent updates. Aborting...")
            return [], last_modified_genre

        last_modified_genre = modified_genres[-1].modified

    return modified_genres, last_modified_genre


def genre_etl(
    es_client: ElasticSearchClient,
    redis_storage: RedisStateStorage,
    psql_client: PostgresClient,
    default_date: dt.datetime,
):
    while True:
        last_modified_genre = _get_latest_state(redis_storage, default_date)
        genre_data, last_modified_genre = _get_person_data(
            psql_client, last_modified_genre
        )
        if len(genre_data) == 0:
            break

        es_ready_data = GenreTransformer(genre_data).get_es_ready_data()

        with es_client as client:
            client.bulk_add_data(es_ready_data)

        with redis_storage as storage:
            State(storage).set_state("genre_last_modified_genre", last_modified_genre)
        logger.info(
            "Iteration ended. " f"Sleeping for: {settings.time_between_executions}"
        )
        time.sleep(settings.time_between_executions)
