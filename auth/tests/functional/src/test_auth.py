import asyncio
import pytest


pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.mark.parametrize(
    "data, expected_answer",
    [
        (
            {"login": "test", "password": "test"},
            {
                "status": 201,
                "body": {
                    "login": "test",
                    "first_name": None,
                    "last_name": None,
                    "roles": [],
                },
            },
        ),
        (
            {"login": "test", "password": "test"},
            {
                "status": 409,
                "body": {"detail": "Login already exists"},
            },
        ),
    ],
)
async def test_signup(create_db, make_post_request, data, expected_answer):
    body, _, status = await make_post_request("users/signup", json=data)

    assert status == expected_answer["status"]
    body.pop("id", None)
    assert body == expected_answer["body"]


@pytest.mark.parametrize(
    "data, expected_answer",
    [
        ({"username": "test2", "password": "test"}, {"status": 200}),
        (
            {"username": "test2", "password": "wrong_password"},
            {"status": 403, "detail": "Invalid password"},
        ),
        (
            {"username": "test3", "password": "wrong_password"},
            {"status": 404, "detail": "Login not found"},
        ),
    ],
)
async def test_login(
    create_user_if_not_exist, make_post_request, data, expected_answer
):
    await create_user_if_not_exist("test2", data["password"])

    body, _, status = await make_post_request("users/login", data=data)

    assert status == expected_answer["status"]

    if expected_answer["status"] == 200:
        assert "access_token" in body.keys()
        assert "token_type" in body.keys()
        assert "refresh_token" in body.keys()
        assert body["token_type"] == "bearer"
    else:
        assert body["detail"] == expected_answer["detail"]


@pytest.mark.parametrize(
    "data, expected_answer",
    [[{"username": "test3", "password": "test"}, {"status": 200}]],
)
async def test_logout(
    create_user_if_not_exist, make_post_request, data, expected_answer
):
    await create_user_if_not_exist("test3", "test")
    body, _, _ = await make_post_request("users/login", data=data)
    print(body)

    headers = {
        "authorization": body["access_token"],
        "refresh-token": body["refresh_token"],
    }

    body, _, status = await make_post_request("users/logout", headers=headers)

    assert status == expected_answer["status"]


@pytest.mark.parametrize(
    "data, expected_answer",
    [
        (
            {
                "username": "test4",
                "password": "test",
                "sleep": 0,
                "real_token": True,
                "logout": False,
            },
            {"status": 200, "login": "test4", "roles": [], "detail": ""},
        ),
        (
            {
                "username": "test4",
                "password": "test",
                "sleep": 1,
                "real_token": True,
                "logout": False,
            },
            {"status": 401, "detail": "Expired token"},
        ),
        (
            {
                "username": "test4",
                "password": "test",
                "sleep": 0,
                "real_token": False,
                "logout": False,
            },
            {"status": 403, "detail": "Invalid token"},
        ),
        (
            {
                "username": "test4",
                "password": "test",
                "sleep": 0,
                "real_token": True,
                "logout": True,
            },
            {"status": 403, "detail": "User logged out"},
        ),
    ],
)
async def test_validate(
    create_user_if_not_exist, make_post_request, data, expected_answer
):
    await create_user_if_not_exist("test4", "test")

    if data["real_token"]:
        login_data = {
            "username": data["username"],
            "password": data["password"],
        }
        body, _, _ = await make_post_request("users/login", data=login_data)
        validate_data = {"access_token": body["access_token"]}
    else:
        validate_data = {"access_token": "fake_token"}

    if data["logout"]:
        headers = {
            "authorization": body["access_token"],
            "refresh-token": body["refresh_token"],
        }
        _, _, _ = await make_post_request("users/logout", headers=headers)

    await asyncio.sleep(data["sleep"] * 60)
    body, _, status = await make_post_request(
        "users/validate", json=validate_data
    )

    assert status == expected_answer["status"]
    if expected_answer["status"] == 200:
        assert body["login"] == expected_answer["login"]
        assert body["roles"] == expected_answer["roles"]
    else:
        assert body["detail"] == expected_answer["detail"]


@pytest.mark.parametrize(
    "data, expected_answer",
    [
        (
            {
                "username": "test5",
                "password": "test",
                "use_twice": False,
                "real_token": True,
                "logout": False,
            },
            {"status": 200},
        ),
        (
            {
                "username": "test5",
                "password": "test",
                "use_twice": True,
                "real_token": True,
                "logout": False,
            },
            {"status": 403, "detail": "Invalid refresh token"},
        ),
        (
            {
                "username": "test5",
                "password": "test",
                "use_twice": False,
                "real_token": False,
                "logout": False,
            },
            {"status": 403, "detail": "Invalid refresh token"},
        ),
    ],
)
async def test_refresh(
    create_user_if_not_exist, make_post_request, data, expected_answer
):
    await create_user_if_not_exist("test5", "test")

    if data["real_token"]:
        login_data = {
            "username": data["username"],
            "password": data["password"],
        }
        body, _, _ = await make_post_request("users/login", data=login_data)
        headers = {
            "refresh-token": body["refresh_token"],
        }
    else:
        headers = {
            "refresh-token": "fake_token",
        }

    if data["logout"]:
        logout_headers = {
            "authorization": body["access_token"],
            "refresh-token": body["refresh_token"],
        }
        _, _, _ = await make_post_request(
            "users/logout", headers=logout_headers
        )

    body, _, status = await make_post_request("users/refresh", headers=headers)
    if data["use_twice"]:
        body, _, status = await make_post_request(
            "users/refresh", headers=headers
        )

    print(body)
    assert status == expected_answer["status"]
    if expected_answer["status"] == 200:
        assert "access_token" in body.keys()
        assert "refresh_token" in body.keys()
        assert "token_type" in body.keys()
    else:
        assert body["detail"] == expected_answer["detail"]


@pytest.mark.parametrize(
    "data, expected_answer",
    [
        (
            {
                "username": "test6",
                "password": "test",
                "login_times": 1,
                "real_token": True,
                "logout": False,
            },
            {"status": 200, "login_times": 1},
        ),
        (
            {
                "username": "test6",
                "password": "test",
                "login_times": 1,
                "real_token": False,
                "logout": False,
            },
            {"status": 401, "detail": "Not authenticated"},
        ),
        (
            {
                "username": "test7",
                "password": "test",
                "login_times": 5,
                "real_token": True,
                "logout": False,
            },
            {"status": 200, "login_times": 5},
        ),
        (
            {
                "username": "test6",
                "password": "test",
                "login_times": 1,
                "real_token": True,
                "logout": True,
            },
            {"status": 403, "detail": "User logged out"},
        ),
    ],
)
async def test_login_history(
    create_user_if_not_exist, make_post_request, data, expected_answer
):
    await create_user_if_not_exist(data["username"], "test")

    if data["real_token"]:
        login_data = {
            "username": data["username"],
            "password": data["password"],
        }
        for _ in range(data["login_times"]):
            body, _, _ = await make_post_request("users/login", data=login_data)
            headers = {
                "authorization": f"Bearer {body['access_token']}",
                "refresh-token": body["refresh_token"],
            }
    else:
        headers = {
            "authorization": "fake_token",
            "refresh-token": "fake_token",
        }

    if data["logout"] and data["real_token"]:
        logout_headers = {
            "authorization": body["access_token"],
            "refresh-token": body["refresh_token"],
        }
        _, _, _ = await make_post_request(
            "users/logout", headers=logout_headers
        )

    body, _, status = await make_post_request(
        "users/login-history", headers=headers
    )

    assert status == expected_answer["status"]
    if expected_answer["status"] == 200:
        assert len(body["logins"]) == expected_answer["login_times"]
    else:
        assert body["detail"] == expected_answer["detail"]


@pytest.mark.parametrize(
    "data, expected_answer",
    [
        (
            {
                "username": "test7",
                "password": "test",
                "real_token": True,
                "logout": False,
                "sleep": 0,
                "body": {
                    "login": "completely_new_login",
                    "password": "test",
                    "first_name": "new_first_name",
                    "last_name": "new_last_name",
                },
            },
            {
                "status": 200,
                "login_times": 1,
                "body": {
                    "login": "completely_new_login",
                    "first_name": "new_first_name",
                    "last_name": "new_last_name",
                    "roles": [],
                },
            },
        ),
        (
            {
                "username": "test7",
                "password": "test",
                "real_token": False,
                "logout": False,
                "sleep": 0,
                "body": {
                    "login": "test6",
                    "password": "new_password",
                    "first_name": "new_first_name",
                    "last_name": "new_last_name",
                },
            },
            {"status": 401, "detail": "Not authenticated"},
        ),
        (
            {
                "username": "test7",
                "password": "test",
                "real_token": True,
                "logout": False,
                "sleep": 1,
                "body": {
                    "login": "completely_new_login",
                    "password": "new_password",
                    "first_name": "new_first_name",
                    "last_name": "new_last_name",
                },
            },
            {"status": 401, "detail": "Expired token"},
        ),
        (
            {
                "username": "test7",
                "password": "test",
                "real_token": True,
                "logout": True,
                "sleep": 0,
                "body": {
                    "login": "completely_new_login",
                    "password": "new_password",
                    "first_name": "new_first_name",
                    "last_name": "new_last_name",
                },
            },
            {"status": 403, "detail": "User logged out"},
        ),
    ],
)
async def test_update_details(
    create_user_if_not_exist,
    make_patch_request,
    make_post_request,
    data,
    expected_answer,
):
    await create_user_if_not_exist(data["username"], "test")

    if data["real_token"]:
        login_data = {
            "username": data["username"],
            "password": data["password"],
        }
        body, _, _ = await make_post_request("users/login", data=login_data)
        headers = {
            "authorization": f"Bearer {body['access_token']}",
            "refresh-token": body["refresh_token"],
        }
    else:
        headers = {
            "authorization": "fake_token",
            "refresh-token": "fake_token",
        }

    if data["logout"] and data["real_token"]:
        logout_headers = {
            "authorization": body["access_token"],
            "refresh-token": body["refresh_token"],
        }
        _, _, _ = await make_post_request(
            "users/logout", headers=logout_headers
        )

    await asyncio.sleep(60 * data["sleep"])

    body, _, status = await make_patch_request(
        "users/update-details", headers=headers, json=data["body"]
    )

    assert status == expected_answer["status"]
    if expected_answer["status"] == 200:
        body.pop("id", None)
        assert body == expected_answer["body"]
    else:
        assert body["detail"] == expected_answer["detail"]


@pytest.mark.parametrize(
    "data, expected_answer",
    [
        (
            {
                "username": "test8",
                "password": "test",
                "real_token": True,
                "logout": False,
                "sleep": 0,
            },
            {
                "status": 200,
                "login_times": 1,
                "body": {
                    "login": "test8",
                    "first_name": None,
                    "last_name": None,
                    "roles": [],
                },
            },
        ),
        (
            {
                "username": "test8",
                "password": "test",
                "real_token": False,
                "logout": False,
                "sleep": 0,
            },
            {"status": 401, "detail": "Not authenticated"},
        ),
        (
            {
                "username": "test7",
                "password": "test",
                "real_token": True,
                "logout": False,
                "sleep": 1,
            },
            {"status": 401, "detail": "Expired token"},
        ),
        (
            {
                "username": "test7",
                "password": "test",
                "real_token": True,
                "logout": True,
                "sleep": 0,
            },
            {"status": 403, "detail": "User logged out"},
        ),
    ],
)
async def test_get_details(
    create_user_if_not_exist,
    make_get_request,
    make_post_request,
    data,
    expected_answer,
):
    await create_user_if_not_exist(data["username"], "test")

    if data["real_token"]:
        login_data = {
            "username": data["username"],
            "password": data["password"],
        }
        body, _, _ = await make_post_request("users/login", data=login_data)
        headers = {
            "authorization": f"Bearer {body['access_token']}",
            "refresh-token": body["refresh_token"],
        }
    else:
        headers = {
            "authorization": "fake_token",
            "refresh-token": "fake_token",
        }

    if data["logout"] and data["real_token"]:
        logout_headers = {
            "authorization": body["access_token"],
            "refresh-token": body["refresh_token"],
        }
        _, _, _ = await make_post_request(
            "users/logout", headers=logout_headers
        )

    await asyncio.sleep(60 * data["sleep"])

    body, _, status = await make_get_request(
        "users/get-details", headers=headers
    )

    assert status == expected_answer["status"]
    if expected_answer["status"] == 200:
        body.pop("id", None)
        assert body == expected_answer["body"]
    else:
        assert body["detail"] == expected_answer["detail"]
