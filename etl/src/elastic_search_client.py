"""
Класс для взаимодействия с Elasticsearch.
Реализует возможность создать индекс и сделать bulk загрузку данных.
Вообще, можно было бы использовать уже готовую библиотеку:
https://elasticsearch-py.readthedocs.io/en/v8.14.0/, но в данном классе
все взаимодействие построено на самостоятельно написанных HTTP запросах.
"""

import json

import requests
from loguru import logger
from src.constants import IndexNames, settings
from src.exceptions import BulkUploadFailed
from src.utils import backoff


class ElasticSearchClient:
    def __init__(self, host: str, port: str):
        self.url = f"http://{host}:{port}"

    @backoff()
    def __enter__(self):
        logger.info("Creating session with elasticsearch")
        self.session = requests.session()
        headers = {"Content-Type": "application/json"}
        self.session.headers.update(headers)
        logger.info("Connection created")
        return self

    def __exit__(self, *args):
        if self.session:
            logger.info("Closing session with elasticsearch")
            self.session.close()
            logger.info("Connection closed")

    @backoff()
    def _check_index_existance(self, url: str) -> bool:
        response = self.session.get(url)
        if response.status_code == 200:
            return True
        return False

    def _get_index_schema(self, index_name: IndexNames) -> dict:
        index_path = settings.elasticsearch_indices.get(index_name)
        if index_path is None:
            raise FileNotFoundError("Missing index schema")
        if not index_path.exists():
            raise FileNotFoundError("Missing index schema")
        with open(index_path, "r") as file:
            index_schema = json.load(file)

        return index_schema

    @backoff()
    def bulk_add_data(self, data: str) -> None:
        """Bulk загрузка данных.

        Parameters
        ----------
        data : str
            Данные которые должны быть загружены

        Raises
        ------
        BulkUploadFailed
            Если произошла ошибка, будет поднято исключение
        """
        logger.info("Bulk adding data")
        url = f"{self.url}/_bulk?filter_path=items.*.error"

        response = self.session.post(url, data=data)
        logger.info(f"Bulk add status code: {response.status_code}")
        if response.status_code != 200 or len(response.text) > 2:
            raise BulkUploadFailed(f"Response text: {response.text}")

    @backoff()
    def create_index(self, index_name: IndexNames) -> None:
        """Функция создающая индекс в Elasticsearch в соответствии со схемой.
        Если индекс уже существует, повторного создания не будет.

        Parameters
        ----------
        index_name : str
            Название индекса
        index_config : dict
            Схема индекса
        """

        url = f"{self.url}/{index_name.value}"

        if self._check_index_existance(url):
            logger.info(f"Index {index_name.value} already exists. Skipping...")
            return

        logger.info(f"Creating index: {index_name.value}")
        index_schema = self._get_index_schema(index_name)

        response_index = self.session.put(url, json=index_schema)
        logger.info(f"Create index status code: {response_index.status_code}")
        if response_index.status_code != 200:
            logger.warning(f"Response text: {response_index.text}")
