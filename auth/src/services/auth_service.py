import jwt
import json

import httpx
import secrets
import datetime as dt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from functools import lru_cache, wraps
from redis.asyncio import Redis
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

import google.auth
import google.oauth2.credentials
import google_auth_oauthlib.flow

from db.redis import get_redis
from db.postgres import async_session
from core.config import settings
from exceptions import (
    LoggedOut,
    InvalidToken,
    ExpiredToken,
    InvalidRefreshToken,
)

from services.user_service import get_user_service, UserService
from schemas.auth import OAuthUserDetails, OAuthProviders, TokenPayload

SEC_IN_MIN = 60


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


class AuthService:
    def __init__(self, redis: Redis, user_service: UserService) -> None:
        self.redis = redis
        self.user_service = user_service

    def generate_token(self, login: str, roles: list[str]):
        to_encode = {"login": login, "roles": roles}
        expire = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
            minutes=settings.token_expire
        )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.jwt_secret, algorithm=settings.algorithm
        )
        return encoded_jwt

    async def generate_refresh_token(self, login: str, roles: list[str]):
        token = secrets.token_hex(32)
        details = json.dumps({"login": login, "roles": roles})
        await self.redis.setex(
            f"refresh:{token}", settings.refresh_expire * SEC_IN_MIN, details
        )
        return token

    def get_token_payload(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token, settings.jwt_secret, algorithms=[settings.algorithm]
            )
        except ExpiredSignatureError:
            raise ExpiredToken
        except InvalidTokenError:
            raise InvalidToken

        return payload

    async def is_token_valid(self, token: str) -> TokenPayload:
        check_logout = await self.redis.get(f"logout:{token}")
        if check_logout is not None:
            raise LoggedOut
        payload = self.get_token_payload(token)
        user_login = payload["login"]
        user = await self.user_service.get_user_from_db(login=user_login)
        user_roles = [role.name for role in user.roles]

        return TokenPayload(login=user_login, roles=user_roles)

    async def logout(self, token: str, refresh_token: str) -> None:
        await self.redis.delete(f"refresh:{refresh_token}")
        await self.redis.setex(
            f"logout:{token}", settings.token_expire * SEC_IN_MIN, ""
        )

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        check_refresh = await self.redis.get(f"refresh:{refresh_token}")
        if check_refresh is None:
            raise InvalidRefreshToken
        payload = json.loads(check_refresh)
        access_token = self.generate_token(payload["login"], payload["roles"])
        new_refresh = await self.generate_refresh_token(
            payload["login"], payload["roles"]
        )
        await self.redis.delete(f"refresh:{refresh_token}")
        return access_token, new_refresh

    async def get_google_oauth_authorization_url(self) -> tuple[str, str]:
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            settings.google_client_config_path,
            scopes=settings.google_oauth_scopes,
        )
        flow.redirect_uri = (
            f"{settings.oauth_redirect_uri}?"
            f"oauth_provider={OAuthProviders.GOOGLE.value}"
        )

        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return authorization_url, state

    async def authenticate_with_google(
        self, state: str, authorization_response: str
    ) -> google.auth.external_account_authorized_user.Credentials:
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            settings.google_client_config_path,
            scopes=settings.google_oauth_scopes,
            state=state,
        )
        flow.redirect_uri = (
            f"{settings.oauth_redirect_uri}?"
            f"oauth_provider={OAuthProviders.GOOGLE.value}"
        )
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials
        return credentials

    async def get_user_info_from_google(
        self,
        token: str,
    ) -> OAuthUserDetails | None:
        url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
        try:
            user_info = response.json()
            user_info["oauth_provider"] = "google"
        except json.JSONDecodeError:
            return None
        user_info = OAuthUserDetails.model_validate(user_info)
        return user_info


@lru_cache()
def get_auth_service(
    redis: Redis = Depends(get_redis),
    user_service: UserService = Depends(get_user_service),
) -> AuthService:
    return AuthService(redis, user_service)


def authorize(roles: list[str]):
    def wrapper(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            async with async_session() as session:
                user_service = UserService(session)
                auth_service = get_auth_service(
                    redis=await get_redis(),
                    user_service=user_service,
                )
                authorization = kwargs.get("authorization")
                if authorization is None:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Missing token",
                    )
                try:
                    payload = await auth_service.is_token_valid(authorization)
                    user_roles = payload.roles
                    intersection = set(roles).intersection(user_roles)
                    if not intersection:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Unauthorized user",
                        )
                except ExpiredToken:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Expired token",
                    )
                except InvalidToken:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Invalid token",
                    )
                except LoggedOut:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="User logged out",
                    )
            return await func(*args, **kwargs)

        return inner

    return wrapper
