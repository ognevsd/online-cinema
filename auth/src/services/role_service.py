from functools import lru_cache
from typing import Sequence
from uuid import UUID

from fastapi import Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_session
from models.entity import Role
from exceptions import RoleExists, RoleNotFound


class RoleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_role_from_db(self, name: str) -> Role | None:
        statement = select(Role).filter(Role.name == name)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_role_by_id(self, id: UUID) -> Role | None:
        statement = select(Role).filter(Role.id == id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_roles_by_ids(self, role_ids: list[UUID]) -> Sequence[Role]:
        statement = select(Role).filter(Role.id.in_(role_ids))
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def add(self, name: str, description: str) -> Role:
        if await self.get_role_from_db(name) is not None:
            raise RoleExists

        role = Role(name=name, description=description)
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)

        return role

    async def delete(self, role_id: UUID):
        if await self.get_role_by_id(role_id) is None:
            raise RoleNotFound

        statement = delete(Role).filter(Role.id == role_id)
        await self.session.execute(statement)
        await self.session.commit()

    async def update(
        self, id: UUID, name: str | None, description: str | None
    ) -> Role:
        role = await self.get_role_by_id(id)
        if role is None:
            raise RoleNotFound

        if name is not None:
            role.name = name  # type: ignore

        if description is not None:
            role.description = description  # type: ignore

        await self.session.commit()
        return role

    async def get_all(self) -> Sequence[Role]:
        statement = select(Role)
        result = await self.session.execute(statement)
        return result.scalars().all()


@lru_cache()
def get_role_service(
    session: AsyncSession = Depends(get_session),
) -> RoleService:
    return RoleService(session)
