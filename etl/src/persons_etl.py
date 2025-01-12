import datetime as dt
import time

from loguru import logger
from src.constants import settings
from src.data_description import FullPersonInfo
from src.data_transformer import PersonTransformer
from src.elastic_search_client import ElasticSearchClient
from src.postgres_client import PostgresClient
from src.state_manager import RedisStateStorage, State


def _get_latest_state(
    storage: RedisStateStorage, default_date: dt.datetime
) -> dt.datetime:
    with storage:
        last_modified_person = State(storage).get_state("persons_last_modified_person")
        logger.info(f"Last modified person: {last_modified_person}")

    if last_modified_person is None:
        last_modified_person = default_date

    return last_modified_person


def _get_person_data(
    client: PostgresClient,
    last_modified_person: dt.datetime,
) -> tuple[list[FullPersonInfo], dt.datetime]:
    with client:
        modified_persons = client.query_modified_people(last_modified_person)

        logger.info(f"Queried: {len(modified_persons)} persons")
        if len(modified_persons) == 0:
            logger.info("No recent updates. Aborting...")
            return [], last_modified_person

        last_modified_person = modified_persons[-1].modified
        person_ids = [person.uuid for person in modified_persons]

        persons_data = client.query_full_person_info(person_ids)

    return persons_data, last_modified_person


def person_etl(
    es_client: ElasticSearchClient,
    redis_storage: RedisStateStorage,
    psql_client: PostgresClient,
    default_date: dt.datetime,
):
    while True:
        last_modified_person = _get_latest_state(redis_storage, default_date)
        persons_data, last_modified_person = _get_person_data(
            psql_client, last_modified_person
        )
        if len(persons_data) == 0:
            break

        es_ready_data = PersonTransformer(persons_data).get_es_ready_data()

        with es_client as client:
            client.bulk_add_data(es_ready_data)

        with redis_storage as storage:
            State(storage).set_state(
                "persons_last_modified_person", last_modified_person
            )
        logger.info(
            "Iteration ended. " f"Sleeping for: {settings.time_between_executions}"
        )
        time.sleep(settings.time_between_executions)
