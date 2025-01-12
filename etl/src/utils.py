import json
import random
from functools import wraps
from time import sleep
from uuid import UUID

import psycopg
import requests
from loguru import logger


def random_jitter(value: float) -> float:
    """Jitter the value a random number of milliseconds.

    This adds up to 1 second of additional time to the original value.
    Prior to backoff version 1.2 this was the default jitter behavior.

    Args:
        value: The unadulterated backoff value.
    """
    return value + random.random()


def backoff(
    start_sleep_time=0.1,
    factor=2,
    border_sleep_time=10,
    max_retries=10,
    exceptions: tuple = (
        ConnectionError,
        psycopg.OperationalError,
        psycopg.DatabaseError,
        requests.HTTPError,
        requests.exceptions.ConnectTimeout,
    ),
):
    """
    Функция для повторного выполнения функции через некоторое время,
    если возникла ошибка. Использует наивный экспоненциальный рост времени
    повтора (factor) до граничного времени ожидания (border_sleep_time)

    Формула:
        t = start_sleep_time * (factor ^ n), если t < border_sleep_time
        t = border_sleep_time, иначе
    :param start_sleep_time: начальное время ожидания
    :param factor: во сколько раз нужно увеличивать время ожидания на каждой
                   итерации
    :param border_sleep_time: максимальное время ожидания
    :return: результат выполнения функции
    """

    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            sleep_time = start_sleep_time
            attempt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt > max_retries:
                        raise
                    sleep_time = random_jitter(sleep_time) * factor
                    if sleep_time > border_sleep_time:
                        sleep_time = border_sleep_time

                    logger.error(f"Error occured during connection: {e}")
                    logger.error(
                        f"Attempt {attempt} failed. Retryin in {sleep_time} " "seconds"
                    )
                    sleep(sleep_time)

        return inner

    return func_wrapper


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return json.JSONEncoder.default(self, obj)
