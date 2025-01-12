from functools import lru_cache
from uuid import UUID

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions import UserExists, UserNotFound, WrongPassword, InvalidOauth
from db.postgres import get_session

from models.entity import Role, User, LoginRecord, AuthProvider
from schemas.entity import UserCreate, UserInDB, UserUpdate
from schemas.auth import OAuthUserDetails, OAuthProviders


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_from_db(
        self, login: str, email: str | None = None
    ) -> User:
        if email is not None:
            statement = select(User).filter(User.email == email)
        else:
            statement = select(User).filter(User.login == login)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_from_db_by_id(self, user_id: UUID) -> User:
        statement = select(User).filter(User.id == user_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create_user(self, user_create: UserCreate) -> User:
        if await self.get_user_from_db(user_create.login) is not None:
            raise UserExists
        user_dto = jsonable_encoder(user_create)
        user = User(**user_dto)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def create_user_oauth(
        self, user_info: OAuthUserDetails, oauth_provider: OAuthProviders
    ) -> User:
        if (
            await self.get_user_from_db(login="", email=user_info.email)
            is not None
        ):
            raise UserExists

        user = User(
            login=user_info.email,
            email=user_info.email,
            password="",
            first_name=user_info.given_name,
            last_name=user_info.family_name,
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        auth_provider_details = AuthProvider(
            user_id=user.id,
            service=OAuthProviders.GOOGLE.value,
            sub=user_info.sub,
        )
        self.session.add(auth_provider_details)
        await self.session.commit()

        return user

    async def validate_user(self, login: str, password: str) -> UserInDB:
        user = await self.get_user_from_db(login)
        if user is None:
            raise UserNotFound
        if not user.check_password(password):
            raise WrongPassword
        return user

    async def validate_oauth_user(
        self, user_info: OAuthUserDetails, oauth_provider: OAuthProviders
    ):
        user = await self.get_user_from_db(login="", email=user_info.email)
        user_auth_provider = list(user.auth_provider)[0]
        if (
            user_auth_provider.sub == user_info.sub
            and user_auth_provider.service == oauth_provider.value
        ):
            return user
        else:
            raise InvalidOauth

    async def update_login_history(self, user: UserInDB, user_agent: str):
        record = LoginRecord(user_id=user.id, user_agent=user_agent)
        self.session.add(record)
        await self.session.commit()

    async def update_details(self, login: str, user_update: UserUpdate) -> User:
        user = await self.get_user_from_db(login)
        if user is None:
            raise UserNotFound

        if user_update.login is not None:
            if await self.get_user_from_db(user_update.login) is not None:
                raise UserExists
            user.login = user_update.login

        if user_update.password is not None:
            user.update_password(user_update.password)

        if user_update.first_name is not None:
            user.first_name = user_update.first_name

        if user_update.last_name is not None:
            user.last_name = user_update.last_name

        await self.session.commit()
        return user

    async def update_roles(self, user_id: UUID, new_roles=list[Role]) -> User:
        user = await self.get_user_from_db_by_id(user_id)
        if user is None:
            raise UserNotFound

        user.roles = new_roles

        await self.session.commit()
        await self.session.refresh(user)

        return user


@lru_cache()
def get_user_service(
    session: AsyncSession = Depends(get_session),
) -> UserService:
    return UserService(session)
