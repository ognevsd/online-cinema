import pytest_asyncio

from sqlalchemy.sql import text, select
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

from typing import AsyncGenerator

from functional.utils.models import Base, User, Role
from functional.settings import settings


@pytest_asyncio.fixture(name="create_db", scope="session")
async def create_db():
    dsn = (
        f"postgresql+asyncpg://{settings.psql_user}:{settings.psql_password}@"
        f"{settings.psql_host}:{settings.psql_port}/{settings.psql_db_name}"
    )
    engine = create_async_engine(dsn, echo=False)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS users"))
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP SCHEMA IF EXISTS users CASCADE"))


@pytest_asyncio.fixture(name="db_session", scope="session")
async def db_session(create_db) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        bind=create_db, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(name="create_role_if_not_exist")
def create_role_if_not_exist(db_session):
    async def inner(name: str):
        statement = select(Role).filter(Role.name == name)
        result = await db_session.execute(statement)
        role = result.scalar_one_or_none()
        if role is None:
            role = Role(name=name)
            db_session.add(role)
            await db_session.commit()
            await db_session.refresh(role)
        return role

    return inner


@pytest_asyncio.fixture(name="create_user_if_not_exist")
def create_user_if_not_exist(db_session, create_role_if_not_exist):
    async def inner(login: str, password: str, roles: list[str] | None = None):
        statement = select(User).filter(User.login == login)
        result = await db_session.execute(statement)
        user = result.scalar_one_or_none()
        if user is None:
            user = User(login=login, password=password)
            db_session.add(user)
            await db_session.commit()
            await db_session.refresh(user)
        if roles is not None:
            role_list = [
                await create_role_if_not_exist(role_name) for role_name in roles
            ]
            user.roles = role_list
            await db_session.commit()
            await db_session.refresh(user)

    return inner
