"""
Класс, реализующий хранение состояния в redis.
"""

import abc
import datetime as dt
from typing import Any, Dict

import redis
from loguru import logger
from src.utils import backoff


class BaseStorage(abc.ABC):
    """Абстрактное хранилище состояния.

    Позволяет сохранять и получать состояние.
    Способ хранения состояния может варьироваться в зависимости
    от итоговой реализации. Например, можно хранить информацию
    в базе данных или в распределённом файловом хранилище.
    """

    @abc.abstractmethod
    def save_state(self, state: Dict[str, Any]) -> None:
        """Сохранить состояние в хранилище."""

    @abc.abstractmethod
    def retrieve_state(self) -> Dict[str, Any]:
        """Получить состояние из хранилища."""


class RedisStateStorage(BaseStorage):
    """Реализация хранилища, использующего Redis.

    Parameters
    ----------
    BaseStorage :
        Абстрактное описание хранилища
    """

    def __init__(self, host, port):
        self.host = host
        self.port = port

    @backoff()
    def __enter__(self):
        logger.info("Creating connection with redis")
        self.client = redis.StrictRedis(self.host, self.port)
        logger.info("Connection created")
        return self

    def __exit__(self, *args):
        if self.client:
            logger.info("Closing connection with redis")
            self.client.close()
            logger.info("Connection closed")

    @backoff()
    def save_state(self, state: Dict[str, dt.datetime]) -> None:
        for key, value in state.items():
            value_str = value.isoformat()
            self.client.set(key, value_str)
            logger.info(f"State saved: {key} - {value_str}")

    @backoff()
    def retrieve_state(self) -> Dict[str, dt.datetime]:
        keys = self.client.keys("*")
        all_values = {}

        if len(keys) == 0:  # type: ignore
            return {}

        for key in keys:  # type: ignore
            value = self.client.get(key)
            value = value.decode("utf-8")  # type: ignore
            logger.info(f"Value retrieved: {key} - {value}")
            all_values[key.decode("utf-8")] = dt.datetime.fromisoformat(value)

        return all_values


class State:
    """Класс для работы с состояниями."""

    def __init__(self, storage: BaseStorage) -> None:
        self.storage = storage
        self.state = self.storage.retrieve_state()

    def set_state(self, key: str, value: Any) -> None:
        """Установить состояние для определённого ключа."""
        self.state[key] = value
        self.storage.save_state(self.state)

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу."""
        return self.state.get(key)
