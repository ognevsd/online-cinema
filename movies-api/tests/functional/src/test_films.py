import pytest

from functional.settings import test_settings

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.mark.parametrize(
    "query_data, expected_answer",
    [
        (
            {"query": "The Star", "page_number": 1, "page_size": 50},
            {"status": 200, "length": 50, "page_number": 1, "total_pages": 2},
        ),
        (
            {"query": "Mashed potato", "page_number": 1, "page_size": 50},
            {"status": 200, "length": 0, "page_number": 1, "total_pages": 0},
        ),
        (
            {"query": "The Star", "page_number": 2, "page_size": 10},
            {"status": 200, "length": 10, "page_number": 2, "total_pages": 6},
        ),
    ],
)
async def test_search(
    generate_film_data_for_search,
    es_write_data,
    make_get_request,
    query_data,
    expected_answer,
):
    # 1. Загружаем данные в ES
    await es_write_data(
        generate_film_data_for_search, "movies", "filmwork_index.json"
    )

    # 2. Запрашиваем данные из ES по API
    body, _, status = await make_get_request("films/search", query_data)

    # 3. Проверяем ответ
    assert status == expected_answer["status"]
    assert len(body.get("data")) == expected_answer["length"]
    assert body.get("page_number") == expected_answer["page_number"]
    assert body.get("total_pages") == expected_answer["total_pages"]


@pytest.mark.parametrize(
    "query_data, expected_answer",
    [
        (
            {"sort": "-imdb_rating", "page_number": 1, "page_size": 50},
            {
                "status": 200,
                "length": 50,
                "page_number": 1,
                "total_pages": 2,
                "first_movie_id": "2a090dde-f688-46fe-a9f4-b781a985275e",
            },
        ),
        (
            {"sort": "imdb_rating", "page_number": 1, "page_size": 50},
            {
                "status": 200,
                "length": 50,
                "page_number": 1,
                "total_pages": 2,
                "first_movie_id": "b503ced6-fff1-493a-ad41-73449b55ffee",
            },
        ),
        (
            {
                "sort": "-imdb_rating",
                "page_number": 1,
                "page_size": 50,
                "genre_uuid": "a886d0ec-c3f3-4b16-b973-dedcf5bfa395",
            },
            {
                "status": 200,
                "length": 15,
                "page_number": 1,
                "total_pages": 1,
                "first_movie_id": "c241874f-53d3-411a-8894-37c19d8bf010",
            },
        ),
    ],
)
async def test_all(
    generate_data_from_file,
    es_write_data,
    make_get_request,
    query_data,
    expected_answer,
):
    # 1. Генерируем данные для ES
    bulk_query = generate_data_from_file(
        test_settings.test_data_path / "all_films.json", "movies"
    )
    # 2. Загружаем данные в ES
    await es_write_data(bulk_query, "movies", "filmwork_index.json")

    # 3. Запрашиваем данные из ES по API

    body, _, status = await make_get_request("films/", query_data)

    # 4. Проверяем ответ
    assert status == expected_answer["status"]
    assert len(body.get("data")) == expected_answer["length"]
    assert body.get("page_number") == expected_answer["page_number"]
    assert body.get("total_pages") == expected_answer["total_pages"]
    assert body.get("data")[0]["uuid"] == expected_answer["first_movie_id"]


@pytest.mark.parametrize(
    "query_data, expected_answer",
    [
        (
            {"film_id": "2a090dde-f688-46fe-a9f4-b781a985275e"},
            {
                "status": 200,
                "movie_id": "2a090dde-f688-46fe-a9f4-b781a985275e",
                "body_detail": None,
            },
        ),
        (
            {"film_id": "66279993-20c1-4512-bc6c-6d98b0967df6"},
            {"status": 404, "movie_id": None, "body_detail": "Film not found"},
        ),
    ],
)
async def test_film_id(
    generate_data_from_file,
    es_write_data,
    make_get_request,
    query_data,
    expected_answer,
):
    # 1. Генерируем данные для ES
    bulk_query = generate_data_from_file(
        test_settings.test_data_path / "all_films.json", "movies"
    )
    # 2. Загружаем данные в ES
    await es_write_data(bulk_query, "movies", "filmwork_index.json")

    # 3. Запрашиваем данные из ES по API

    body, _, status = await make_get_request(
        f"films/{query_data['film_id']}", {}
    )

    # 4. Проверяем ответ
    assert status == expected_answer["status"]
    assert body.get("uuid") == expected_answer["movie_id"]
    assert body.get("detail") == expected_answer["body_detail"]
