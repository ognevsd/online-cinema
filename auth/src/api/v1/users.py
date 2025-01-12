import datetime as dt
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Header,
    status,
)
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, Field
from fastapi_pagination import paginate, Page

from services.user_service import get_user_service, UserService
from services.auth_service import get_auth_service, AuthService, oauth2_scheme
from schemas.entity import UserCreate, UserUpdate
from schemas.auth import OAuthProviders
from exceptions import (
    InvalidRefreshToken,
    UserExists,
    UserNotFound,
    WrongPassword,
    LoggedOut,
    InvalidToken,
    ExpiredToken,
    InvalidOauth,
)

router = APIRouter()


class Tokens(BaseModel):
    access_token: str
    token_type: str = Field(default="bearer")
    refresh_token: str


class LoginItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    login_at: dt.datetime
    user_agent: str


class LoginHistory(BaseModel):
    logins: list[LoginItem]


class Role(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    name: str


class UserDetails(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: UUID
    login: str
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    roles: list[Role] = Field(default=[])


class TokenPayload(BaseModel):
    login: str
    roles: list[str]


class ValidateToken(BaseModel):
    access_token: str


@router.post(
    "/signup", response_model=UserDetails, status_code=status.HTTP_201_CREATED
)
async def create_user(
    user_create: UserCreate, db: UserService = Depends(get_user_service)
):
    try:
        user = await db.create_user(user_create)
    except UserExists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Login already exists"
        )
    created_user = UserDetails.model_validate(user)
    return created_user


@router.post("/login", response_model=Tokens)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    db: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        user = await db.validate_user(form_data.username, form_data.password)
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Login not found"
        )
    except WrongPassword:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid password"
        )
    user_agent = request.headers.get("user-agent", "Unknown")
    await db.update_login_history(user, user_agent)
    roles = [role.name for role in user.roles]
    return Tokens(
        access_token=auth_service.generate_token(user.login, roles),
        refresh_token=await auth_service.generate_refresh_token(
            user.login, roles
        ),
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    authorization: str = Header(),
    refresh_token: str = Header(),
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.logout(authorization, refresh_token)


@router.post(
    "/validate", status_code=status.HTTP_200_OK, response_model=TokenPayload
)
async def validate_token(
    token: ValidateToken,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        payload = await auth_service.is_token_valid(token.access_token)
    except ExpiredToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired token"
        )
    except InvalidToken:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token"
        )
    except LoggedOut:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User logged out"
        )
    print(payload.model_dump())
    return TokenPayload.model_validate(payload.model_dump())


@router.post("/refresh", response_model=Tokens)
async def refresh_token(
    refresh_token: str = Header(),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        access_token, refresh_token = await auth_service.refresh_tokens(
            refresh_token
        )
    except InvalidRefreshToken:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid refresh token",
        )
    return Tokens(access_token=access_token, refresh_token=refresh_token)


@router.post("/login-history", response_model=Page[LoginItem])
async def login_history(
    authorization: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    db: UserService = Depends(get_user_service),
):
    try:
        payload = await auth_service.is_token_valid(authorization)
    except InvalidToken:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token"
        )
    except LoggedOut:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User logged out"
        )

    user = await db.get_user_from_db(payload.login)
    login_history = []
    for item in user.logins:
        tmp = LoginItem(login_at=item.login_at, user_agent=item.user_agent)
        login_history.append(tmp)
    return paginate(login_history)


@router.patch("/update-details", response_model=UserDetails)
async def update_user_details(
    user_details: UserUpdate,
    authorization: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    db: UserService = Depends(get_user_service),
):
    try:
        payload = await auth_service.is_token_valid(authorization)
    except ExpiredToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired token"
        )
    except InvalidToken:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token"
        )
    except LoggedOut:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User logged out"
        )
    user = await db.update_details(payload.login, user_details)
    return UserDetails.model_validate(user)


@router.get("/get-details", response_model=UserDetails)
async def get_user_details(
    authorization: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    db: UserService = Depends(get_user_service),
):
    try:
        payload = await auth_service.is_token_valid(authorization)
    except ExpiredToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired token"
        )
    except InvalidToken:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token"
        )
    except LoggedOut:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User logged out"
        )
    user = await db.get_user_from_db(payload.login)
    return UserDetails.model_validate(user)


@router.get("/login-oauth")
async def google_oauth(
    request: Request,
    oauth_provider: OAuthProviders,
    auth_service: AuthService = Depends(get_auth_service),
):
    if oauth_provider == OAuthProviders.GOOGLE:
        (
            redirect_url,
            state,
        ) = await auth_service.get_google_oauth_authorization_url()
        request.session["state"] = state
        return RedirectResponse(url=redirect_url)


@router.get("/oauth2callback")
async def handleoauth2(
    request: Request,
    oauth_provider: OAuthProviders,
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    if oauth_provider == OAuthProviders.GOOGLE:
        state = request.session.get("state", "")
        credentials = await auth_service.authenticate_with_google(
            state, str(request.url)
        )
        user_info = await auth_service.get_user_info_from_google(
            credentials.token
        )
        if user_info is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Oauth failed",
            )

        user = await user_service.get_user_from_db(
            login="", email=user_info.email
        )
        try:
            if user is None:
                user = await user_service.create_user_oauth(
                    user_info, OAuthProviders.GOOGLE
                )
            else:
                user = await user_service.validate_oauth_user(
                    user_info, OAuthProviders.GOOGLE
                )
        except InvalidOauth:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User exists, but oauth details doesn't correspond with exising user",
            )
        except UserExists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Login already exists",
            )

        user_agent = request.headers.get("user-agent", "Unknown")
        await user_service.update_login_history(user, user_agent)
        roles = [role.name for role in user.roles]
        return Tokens(
            access_token=auth_service.generate_token(user.login, roles),
            refresh_token=await auth_service.generate_refresh_token(
                user.login, roles
            ),
        )
