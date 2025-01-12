import json
import uuid
import pytest_asyncio

from pathlib import Path


@pytest_asyncio.fixture(name="generate_film_data_for_search")
def generate_film_data_for_search():
    es_data = [
        {
            "uuid": str(uuid.uuid4()),
            "imdb_rating": 8.5,
            "genre": [
                {"uuid": str(uuid.uuid4()), "name": "Action"},
                {"uuid": str(uuid.uuid4()), "name": "Sci-Fi"},
            ],
            "title": "The Star",
            "description": "New World",
            "directors_names": ["Stan", "George"],
            "actors_names": ["Ann", "Bob"],
            "writers_names": ["Ben", "Howard"],
            "actors": [
                {
                    "uuid": "ef86b8ff-3c82-4d31-ad8e-72b69f4e3f95",
                    "name": "Ann",
                },
                {
                    "uuid": "fb111f22-121e-44a7-b78f-b19191810fbf",
                    "name": "Bob",
                },
            ],
            "directors": [
                {
                    "uuid": "ef86b8ff-3c82-4d31-ad8e-72b69f4e3f95",
                    "name": "Ann",
                },
                {
                    "uuid": "fb111f22-121e-44a7-b78f-b19191810fbf",
                    "name": "Bob",
                },
            ],
            "writers": [
                {
                    "uuid": "caf76c67-c0fe-477e-8766-3ab3ff2574b5",
                    "name": "Ben",
                },
                {
                    "uuid": "b45bd7bc-2e16-46d5-b125-983d356768c6",
                    "name": "Howard",
                },
            ],
        }
        for _ in range(60)
    ]

    bulk_query: list[dict] = []
    for row in es_data:
        data = {"_index": "movies", "_id": row["uuid"]}
        data.update({"_source": row})
        bulk_query.append(data)

    return bulk_query


@pytest_asyncio.fixture(name="generate_data_from_file")
def generate_data_from_file():
    def inner(file_path: Path, index: str):
        with open(file_path, "r") as file:
            es_data = json.load(file)

        bulk_query: list[dict] = []

        for row in es_data:
            data = {"_index": index, "_id": row["uuid"]}
            data.update({"_source": row})
            bulk_query.append(data)

        return bulk_query

    return inner
