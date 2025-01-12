import pytest

from functional.settings import test_settings

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.mark.parametrize(
    "query_data, expected_answer",
    [
        (
            {"query": "George Lucas", "page_number": 1, "page_size": 50},
            {
                "status": 200,
                "length": 26,
                "number_of_films": 46,
                "page_number": 1,
                "total_pages": 1,
            },
        ),
        (
            {"query": "Locas", "page_number": 1, "page_size": 50},
            {
                "status": 200,
                "length": 0,
                "number_of_films": None,
                "page_number": 1,
                "total_pages": 0,
            },
        ),
        (
            {"query": "Lucas", "page_number": 2, "page_size": 1},
            {
                "status": 200,
                "length": 1,
                "number_of_films": 2,
                "page_number": 2,
                "total_pages": 2,
            },
        ),
    ],
)
async def test_search(
    generate_data_from_file,
    es_write_data,
    make_get_request,
    query_data,
    expected_answer,
):
    # 1. Генерируем данные для ES
    bulk_query = generate_data_from_file(
        test_settings.test_data_path / "all_persons.json", "persons"
    )
    # 2. Загружаем данные в ES
    await es_write_data(bulk_query, "persons", "person_index.json")

    # 3. Запрашиваем данные из ES по API

    body, _, status = await make_get_request("persons/search", query_data)

    body_data = body.get("data")

    # 4. Проверяем ответ
    assert status == expected_answer["status"]
    assert len(body.get("data")) == expected_answer["length"]

    if len(body_data) > 0:
        assert (
            len(body_data[0].get("films", []))
            == expected_answer["number_of_films"]
        )
    assert body.get("page_number") == expected_answer["page_number"]
    assert body.get("total_pages") == expected_answer["total_pages"]


@pytest.mark.parametrize(
    "query_data, expected_answer",
    [
        (
            {"person_id": "a5a8f573-3cee-4ccc-8a2b-91cb9f55250a"},
            {
                "status": 200,
                "person_id": "a5a8f573-3cee-4ccc-8a2b-91cb9f55250a",
                "body_detail": None,
            },
        ),
        (
            {"person_id": "a5a8f573-3cee-4ccc-8a2b-91cb9f552509"},
            {
                "status": 404,
                "person_id": None,
                "body_detail": "Person not found",
            },
        ),
    ],
)
async def test_person_id(
    generate_data_from_file,
    es_write_data,
    make_get_request,
    query_data,
    expected_answer,
):
    # 1. Генерируем данные для ES
    bulk_query = generate_data_from_file(
        test_settings.test_data_path / "all_persons.json", "persons"
    )

    # 2. Загружаем данные в ES
    await es_write_data(bulk_query, "persons", "person_index.json")

    # 3. Запрашиваем данные из ES по API

    body, _, status = await make_get_request(
        f"persons/{query_data['person_id']}", {}
    )

    # 4. Проверяем ответ
    assert status == expected_answer["status"]
    assert body.get("uuid") == expected_answer["person_id"]
    assert body.get("detail") == expected_answer["body_detail"]


@pytest.mark.parametrize(
    "query_data, expected_answer",
    [
        (
            {"person_id": "a5a8f573-3cee-4ccc-8a2b-91cb9f55250a"},
            {
                "status": 200,
                "length": 46,
                "body_detail": None,
            },
        ),
        (
            {"person_id": "a5a8f573-3cee-4ccc-8a2b-91cb9f552509"},
            {"status": 404, "length": 0, "body_detail": "Person not found"},
        ),
    ],
)
async def test_person_id_films(
    generate_data_from_file,
    es_write_data,
    make_get_request,
    query_data,
    expected_answer,
):
    # 1. Генерируем данные для ES
    bulk_query = generate_data_from_file(
        test_settings.test_data_path / "all_persons.json", "persons"
    )

    # 2. Загружаем данные в ES
    await es_write_data(bulk_query, "persons", "person_index.json")

    # 3. Запрашиваем данные из ES по API

    body, _, status = await make_get_request(
        f"persons/{query_data['person_id']}", {}
    )

    # 4. Проверяем ответ
    assert status == expected_answer["status"]
    assert len(body.get("films", [])) == expected_answer["length"]
    assert body.get("detail") == expected_answer["body_detail"]
