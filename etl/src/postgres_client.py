import datetime as dt
from uuid import UUID

import psycopg
import psycopg.sql
from loguru import logger
from psycopg.rows import dict_row
from src.constants import settings
from src.data_description import (
    Filmwork,
    FullFilmworkInfo,
    FullPersonInfo,
    Genre,
    Person,
)
from src.utils import backoff


class PostgresClient:
    def __init__(self, dsl: dict):
        self.dsl = dsl

    @backoff()
    def __enter__(self):
        logger.info("Creating connection with psql")
        self.connection = psycopg.connect(
            **self.dsl,
            row_factory=dict_row,
            cursor_factory=psycopg.ClientCursor,
        )
        logger.info("Connection created")
        return self

    def __exit__(self, *args):
        if self.connection:
            logger.info("Closing connection with psql")
            self.connection.close()
            logger.info("Connection closed")

    @backoff()
    def _log_and_execute(self, query: str, parameters: tuple) -> list[dict]:
        """Пишет сообщение в лог и выполняет переданный запрос

        Parameters
        ----------
        query : str
            Запрос, который необходимо выполнить

        Returns
        -------
        list[dict]
            Результат запроса
        """
        logger.debug(f"Executing query: {query.replace('\n', '')}")
        with self.connection.cursor() as cursor:
            cursor.execute(query, parameters)
            return cursor.fetchall()

    def query_modified_people(self, time: dt.datetime) -> list[Person]:
        """Запрашивает людей, данные о которых были изменены после определенной
        даты.

        Parameters
        ----------
        time : dt.datetime
            Дата последнего изменения

        Returns
        -------
        list[Person]
            Список людей. Может быть пустым.
        """
        logger.info(f"Querying list of people with modified field > {time.isoformat()}")
        query = """
        SELECT id as uuid, modified
        FROM content.person
        WHERE modified > %s
        ORDER BY modified
        LIMIT %s;
        """

        result = self._log_and_execute(query, (time.isoformat(), settings.chunk_size))
        return [Person(**item) for item in result]

    @backoff()
    def query_modified_filmworks(self, time: dt.datetime) -> list[FullFilmworkInfo]:
        """Запрашивает фильмы, которые были изменены после определенной даты.

        Parameters
        ----------
        time : dt.datetime
            Дата последнего изменения

        Returns
        -------
        list[FullFilmworkInfo]
            Результат выполнения запроса. Может быть пустым.
        """
        logger.info(
            "Querying list of filmworks with modified field > " f"{time.isoformat()}"
        )
        query = """
        SELECT
            fw.id as uuid,
            fw.title,
            fw.description,
            fw.rating,
            fw.type,
            fw.created,
            fw.modified,
            pfw.role,
            p.id as person_id,
            p.full_name,
            g.id as genre_id,
            g.name as genre_name
        FROM content.film_work fw
        LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
        LEFT JOIN content.person p ON p.id = pfw.person_id
        LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
        LEFT JOIN content.genre g ON g.id = gfw.genre_id
        WHERE fw.modified > %s
        ORDER BY fw.modified
        LIMIT %s;
        """

        result = self._log_and_execute(query, (time.isoformat(), settings.chunk_size))
        return [FullFilmworkInfo(**item) for item in result]

    @backoff()
    def query_filmworks_with_selected_persons(
        self, person_ids: list[UUID]
    ) -> list[Filmwork]:
        """Запрашивает данные о фильмах, в которых встречается id человека из
        списка.

        Parameters
        ----------
        person_ids : list[UUID]
            Список людей, которые должны быть в фильме

        Returns
        -------
        list[Filmwork]
            Результат выполнения запроса. Может быть пустым
        """
        logger.info("Querying list of filmworks")

        query = """
        SELECT fw.id as uuid, fw.modified
        FROM content.film_work fw
        LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
        WHERE pfw.person_id = ANY(%s)
        ORDER BY fw.modified
        LIMIT %s;
        """

        result = self._log_and_execute(query, (person_ids, settings.chunk_size))
        return [Filmwork(**item) for item in result]

    @backoff()
    def query_necessary_filmwork_data(
        self, filmwork_ids: list[UUID]
    ) -> list[FullFilmworkInfo]:
        """Запрашивает все данные о фильмах, id которых был получен как
        параметр

        Parameters
        ----------
        filmwork_ids : list[UUID]
            id фильмов, которые должны быть выгружены

        Returns
        -------
        list[FullFilmworkInfo]
            Результат выполнения запроса. Может быть пустым
        """
        logger.info("Querying all required filmwork data for selected ids")
        query = """
        SELECT
            fw.id as uuid,
            fw.title,
            fw.description,
            fw.rating,
            fw.type,
            fw.created,
            fw.modified,
            pfw.role,
            p.id as person_id,
            p.full_name,
            g.id as genre_id,
            g.name as genre_name
        FROM content.film_work fw
        LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
        LEFT JOIN content.person p ON p.id = pfw.person_id
        LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
        LEFT JOIN content.genre g ON g.id = gfw.genre_id
        WHERE fw.id = ANY(%s);
        """

        result = self._log_and_execute(query, (filmwork_ids,))
        return [FullFilmworkInfo(**item) for item in result]

    @backoff()
    def query_full_person_info(self, person_ids: list[UUID]) -> list[FullPersonInfo]:
        logger.info("Querying list of persons with details")
        query = """
        SELECT
            p.id as uuid,
            p.full_name,
            p.modified,
            pfw.film_work_id as filmwork_id,
            pfw.role
        FROM content.person p
        LEFT JOIN content.person_film_work pfw ON pfw.person_id = p.id
        WHERE p.id = ANY(%s)
        ORDER BY p.modified
        """

        result = self._log_and_execute(query, (person_ids,))
        return [FullPersonInfo(**item) for item in result]

    @backoff()
    def query_genres(self, time: dt.datetime):
        logger.info("Querying list of genres")
        query = """
        SELECT
            g.id as uuid,
            g.name,
            g.description,
            g.modified
        FROM content.genre g
        WHERE g.modified > %s
        ORDER BY g.modified
        LIMIT %s
        """

        result = self._log_and_execute(query, (time, settings.chunk_size))

        return [Genre(**item) for item in result]
