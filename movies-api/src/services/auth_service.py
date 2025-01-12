import json
import httpx
from functools import wraps

from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.config import settings


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: (
            HTTPAuthorizationCredentials | None
        ) = await super().__call__(request)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code.",
            )
        if not credentials.scheme == "Bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Only Bearer token might be accepted",
            )
        token = credentials.credentials
        return token


security_jwt = JWTBearer()


async def get_username(token: str):
    auth_url = (
        f"{settings.auth_service_host}:{settings.auth_service_port}/"
        "api/v1/users/validate"
    )
    payload = {"access_token": token}
    async with httpx.AsyncClient() as client:
        resp = await client.post(auth_url, json=payload)

    try:
        data = resp.json()
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JSON Decode Error",
        )
    return data.get("login")


def authorize(roles: list[str]):
    def wrapper(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            auth_url = (
                f"{settings.auth_service_host}:{settings.auth_service_port}/"
                "api/v1/users/validate"
            )
            authorization = kwargs.get("authorization")
            payload = {"access_token": authorization}
            if authorization is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Missing token",
                )
            async with httpx.AsyncClient() as client:
                resp = await client.post(auth_url, json=payload)

            try:
                data = resp.json()
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="JSON Decode Error",
                )

            if resp.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=data.get("detail"),
                )
            if resp.status_code == 403:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=data.get("detail"),
                )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authorization server error",
                )

            user_roles = data.get("roles")
            intersection = set(roles).intersection(user_roles)
            if not intersection:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Unauthorized user",
                )
            return await func(*args, **kwargs)

        return inner

    return wrapper
