"""
Модуль, который используется для того чтобы преобразовать данные, полученные
из Postgres базы данных и подготовить их к загрузке в Elasticsearch
"""

import json
from collections import defaultdict

from src.constants import IndexNames
from src.data_description import FullFilmworkInfo, FullPersonInfo, Genre
from src.utils import UUIDEncoder


class DataTransformer:
    def __init__(self):
        self._es_ready_data = []

    def get_es_ready_data(self) -> str:
        """Возвращает готовые к bulk загрузке в Elasticsearch данные.

        Returns
        -------
        str
            Данные, сгруппированные для дальнейшей загрузки в Elasticsearch
        """
        bulk_data = []

        for item in self._es_ready_data:
            bulk_data.append(json.dumps(item, cls=UUIDEncoder))
        bulk_data = "\n".join(bulk_data) + "\n"

        return bulk_data


class FilmworkTransformer(DataTransformer):
    def __init__(self, data: list[FullFilmworkInfo]):
        """Конструктор данных о фильмах. Исходные данные имеют большое
        количество почти одинаковых значений. Отличие может быть в жанре или
        в человеке и его роли. Конструктор обрабатывает входные данные таким
        образом чтобы хранился список с уникальными значениями фильмов.
        Также для каждого названия фильма хранится список его жанров и людей.
        У списка людей присутствует дополнительная группировка по роли.

        Parameters
        ----------
        data : list[FullFilmworkInfo]
            Исходные данные, полученные из базы данных
        """
        super().__init__()
        self._data = data
        self._get_filmwork_data()
        self._get_people_for_filmwork()
        self._get_genres_for_filmwork()
        self._map_for_elasticsearch_bulk_upload()

    def _get_filmwork_data(self):
        """Создает список с уникальным набором фильмов и их основными
        характеристиками: id, рейтинг, название, описание.
        """
        self._filmworks = []
        for item in self._data:
            tmp = {
                "uuid": str(item.uuid),
                "imdb_rating": item.rating,
                "title": item.title,
                "description": item.description,
            }
            if tmp not in self._filmworks:
                self._filmworks.append(tmp)

    def _get_people_for_filmwork(self):
        """Cобирает в dict всех людей, относящихся к фильму. Производится
        дополнительная группировка по роли. Ключ - название фильма.
        """
        self._people = defaultdict(lambda: defaultdict(list))
        for item in self._data:
            filmwork = item.title
            role = item.role
            person = {"uuid": str(item.person_id), "name": item.full_name}
            if person not in self._people[filmwork][role]:
                self._people[filmwork][role].append(person)

    def _get_genres_for_filmwork(self):
        """Создает dict с уникальным набором жанров. Ключ - название фильма."""
        self._genres = defaultdict(list)
        for item in self._data:
            genre = {"uuid": item.genre_id, "name": item.genre_name}
            if genre not in self._genres[item.title]:
                self._genres[item.title].append(genre)

    def _map_for_elasticsearch_bulk_upload(self):
        """
        Данные группируются в соответствии со схемой индекса Elasticsearch
        """
        for item in self._filmworks:
            title = item["title"]

            genres = self._genres[title]
            actors = self._people[title]["actor"]
            directors = self._people[title]["director"]
            writers = self._people[title]["writer"]

            item["genre"] = genres
            item["directors"] = directors
            item["actors"] = actors
            item["writers"] = writers
            item["directors_names"] = [x["name"] for x in directors]
            item["writers_names"] = [x["name"] for x in writers]
            item["actors_names"] = [x["name"] for x in actors]

            index_info = {
                "index": {
                    "_index": IndexNames.MOVIES.value,
                    "_id": item["uuid"],
                }
            }

            self._es_ready_data.append(index_info)
            self._es_ready_data.append(item)


class PersonTransformer(DataTransformer):
    def __init__(self, data: list[FullPersonInfo]):
        super().__init__()
        self._data = data
        self._get_person_data()
        self._get_roles_for_filmwork()
        self._map_for_elasticsearch_bulk_upload()

    def _get_person_data(self):
        """Создает список с уникальным набором фильмов и их основными
        характеристиками: id, рейтинг, название, описание.
        """
        self._persons = []
        for item in self._data:
            tmp = {
                "uuid": str(item.uuid),
                "full_name": item.full_name,
            }
            if tmp not in self._persons:
                self._persons.append(tmp)

    def _get_roles_for_filmwork(self):
        """Создает dict с набором фильмов и ролей в фильме.
        Ключ - id человека
        """
        self._films = defaultdict(lambda: defaultdict(list))
        for item in self._data:
            filmwork = str(item.filmwork_id)
            role = item.role
            if role not in self._films[str(item.uuid)][filmwork]:
                self._films[str(item.uuid)][filmwork].append(role)

    def _map_for_elasticsearch_bulk_upload(self):
        """
        Данные группируются в соответствии со схемой индекса Elasticsearch
        """
        for item in self._persons:
            films = []
            for k, v in self._films[item["uuid"]].items():
                tmp = {}
                tmp["uuid"] = k
                tmp["roles"] = v
                films.append(tmp)

            item["films"] = films

            index_info = {
                "index": {
                    "_index": IndexNames.PERSONS.value,
                    "_id": item["uuid"],
                }
            }

            self._es_ready_data.append(index_info)
            self._es_ready_data.append(item)


class GenreTransformer(DataTransformer):
    def __init__(self, data: list[Genre]):
        super().__init__()
        self._data = data
        self._map_for_elasticsearch_bulk_upload()

    def _map_for_elasticsearch_bulk_upload(self):
        """
        Данные группируются в соответствии со схемой индекса Elasticsearch
        """
        for item in self._data:
            genre = {}
            genre["uuid"] = str(item.uuid)
            genre["name"] = item.name
            genre["description"] = item.description

            index_info = {
                "index": {
                    "_index": IndexNames.GENRES.value,
                    "_id": str(item.uuid),
                }
            }

            self._es_ready_data.append(index_info)
            self._es_ready_data.append(genre)
