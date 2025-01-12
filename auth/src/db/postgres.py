from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

from typing import AsyncGenerator


from core.config import settings

Base = declarative_base()
dsn = (
    f"postgresql+asyncpg://{settings.psql_user}:{settings.psql_password}@"
    f"{settings.psql_host}:{settings.psql_port}/{settings.psql_db_name}"
)

engine = create_async_engine(dsn, echo=True)
async_session = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
