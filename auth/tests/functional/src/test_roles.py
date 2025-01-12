import asyncio
import pytest


pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.mark.parametrize(
    "data, expected_answer",
    [
        (
            {
                "username": "admin",
                "password": "test",
                "roles": ["admin"],
                "real_token": True,
                "logout": False,
                "sleep": 0,
                "role_details": {
                    "name": "new_role",
                    "description": "new description",
                },
            },
            {
                "status": 201,
                "body": {
                    "name": "new_role",
                    "description": "new description",
                },
            },
        ),
        (
            {
                "username": "not_admin",
                "password": "test",
                "roles": None,
                "real_token": True,
                "logout": False,
                "sleep": 0,
                "role_details": {
                    "name": "new_role",
                    "description": "new description",
                },
            },
            {"status": 403, "detail": "Unauthorized user"},
        ),
        (
            {
                "username": "admin",
                "password": "test",
                "roles": ["admin"],
                "real_token": False,
                "logout": False,
                "sleep": 0,
                "role_details": {
                    "name": "new_role",
                    "description": "new description",
                },
            },
            {"status": 401, "detail": "Not authenticated"},
        ),
        (
            {
                "username": "admin",
                "password": "test",
                "roles": ["admin"],
                "real_token": True,
                "logout": False,
                "sleep": 1,
                "role_details": {
                    "name": "new_role",
                    "description": "new description",
                },
            },
            {"status": 401, "detail": "Expired token"},
        ),
        (
            {
                "username": "test7",
                "password": "test",
                "roles": ["admin"],
                "real_token": True,
                "logout": True,
                "sleep": 0,
                "role_details": {
                    "name": "new_role",
                    "description": "new description",
                },
            },
            {"status": 403, "detail": "User logged out"},
        ),
    ],
)
async def test_add_role(
    create_user_if_not_exist,
    make_post_request,
    data,
    expected_answer,
):
    await create_user_if_not_exist(
        data["username"], data["password"], data["roles"]
    )

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

    body, _, status = await make_post_request(
        "roles/add", json=data["role_details"], headers=headers
    )

    assert status == expected_answer["status"]
    if expected_answer["status"] == 200 or expected_answer["status"] == 201:
        body.pop("id", None)
        assert body == expected_answer["body"]
    else:
        assert body["detail"] == expected_answer["detail"]
