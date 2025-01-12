import datetime as dt
import time

from loguru import logger
from src.constants import settings
from src.data_description import FullFilmworkInfo
from src.data_transformer import FilmworkTransformer
from src.elastic_search_client import ElasticSearchClient
from src.postgres_client import PostgresClient
from src.state_manager import RedisStateStorage, State


def _get_latest_state(
    storage: RedisStateStorage, default_date: dt.datetime
) -> tuple[dt.datetime, dt.datetime]:
    with storage:
        last_modified_person = State(storage).get_state("movies_last_modified_person")
        last_modified_filmwork = State(storage).get_state(
            "movies_last_modified_filmwork"
        )
        logger.info(f"Last modified person: {last_modified_person}")
        logger.info(f"Last modified filmwork: {last_modified_filmwork}")

    if last_modified_person is None:
        last_modified_person = default_date
    if last_modified_filmwork is None:
        last_modified_filmwork = default_date

    return last_modified_person, last_modified_filmwork


def _get_filmwork_data(
    client: PostgresClient,
    last_modified_person: dt.datetime,
    last_modified_filmwork: dt.datetime,
) -> tuple[list[FullFilmworkInfo], dt.datetime, dt.datetime]:
    with client:
        filmwork_data = client.query_modified_filmworks(last_modified_filmwork)
        logger.info(f"Queried: {len(filmwork_data)} filmworks")
        if len(filmwork_data) == 0:
            people_list = client.query_modified_people(last_modified_person)
            if len(people_list) == 0:
                logger.info("No recent updates. Aborting...")
                return [], last_modified_person, last_modified_filmwork
            last_modified_person = people_list[-1].modified
            person_ids = [person.uuid for person in people_list]
            filmwork_list = client.query_filmworks_with_selected_persons(person_ids)
            filmwork_ids = [filmwork.uuid for filmwork in filmwork_list]
            filmwork_data = client.query_necessary_filmwork_data(filmwork_ids)
        else:
            last_modified_filmwork = filmwork_data[-1].modified
    return filmwork_data, last_modified_person, last_modified_filmwork


def filmwork_etl(
    es_client: ElasticSearchClient,
    redis_storage: RedisStateStorage,
    psql_client: PostgresClient,
    default_date: dt.datetime,
):
    while True:
        last_modified_person, last_modified_filmwork = _get_latest_state(
            redis_storage, default_date
        )
        filmwork_data, last_modified_person, last_modified_filmwork = (
            _get_filmwork_data(
                psql_client, last_modified_person, last_modified_filmwork
            )
        )
        if len(filmwork_data) == 0:
            break

        es_ready_data = FilmworkTransformer(filmwork_data).get_es_ready_data()

        with es_client as client:
            client.bulk_add_data(es_ready_data)

        with redis_storage as storage:
            State(storage).set_state(
                "movies_last_modified_filmwork", last_modified_filmwork
            )
            State(storage).set_state(
                "movies_last_modified_person", last_modified_person
            )
        logger.info(
            "Iteration ended. " f"Sleeping for: {settings.time_between_executions}"
        )
        time.sleep(settings.time_between_executions)
