import json
from functools import wraps

from pydantic import BaseModel
from pydantic.json import pydantic_encoder
from redis.asyncio import Redis

redis: Redis | None = None

ONE_MINUTE = 60


# Функция понадобится при внедрении зависимостей
async def get_redis() -> Redis:
    return redis


def redis_cache(Model: BaseModel, cache_expire: int = ONE_MINUTE):
    def wrapper(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            redis = await get_redis()
            key_params = [str(args[0]), func.__name__]
            key_params.extend([str(x) for x in args[1:]])
            key = ":".join(str(x) for x in key_params)
            data = await redis.get(key)
            if not data:
                data = await func(*args, **kwargs)
                if data:
                    await redis.set(key, data.model_dump_json(), cache_expire)
            else:
                data = Model.model_validate_json(data)

            return data

        return inner

    return wrapper


def redis_cache_list_and_page(
    Model: BaseModel, cache_expire: int = ONE_MINUTE
):
    def wrapper(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            redis = await get_redis()
            key_params = [str(args[0]), func.__name__]
            key_params.extend([str(x) for x in args[1:]])
            for k, v in kwargs.items():
                key_params.append(f"{k}_{v}")

            key = ":".join(str(x) for x in key_params)
            data = await redis.get(key)
            if not data:
                data = await func(*args, **kwargs)
                if data:
                    await redis.set(
                        key,
                        json.dumps(data, default=pydantic_encoder),
                        cache_expire,
                    )
            else:
                data_json = json.loads(data)
                data = (
                    [Model.model_validate(item) for item in data_json[0]],
                    data_json[1],
                )

            return data

        return inner

    return wrapper
