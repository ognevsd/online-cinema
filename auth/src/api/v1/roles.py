from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from services.auth_service import authorize, oauth2_scheme
from services.user_service import get_user_service, UserService
from services.role_service import get_role_service, RoleService

from exceptions import RoleExists, RoleNotFound


router = APIRouter()


class UserForm(BaseModel):
    id: UUID


class RoleForm(BaseModel):
    id: UUID
    name: str | None = Field(default=None)
    description: str | None = Field(default=None)


class RoleDetails(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: UUID | None = Field(default=None)
    name: str
    description: str | None


class UserDetails(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: UUID
    login: str
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    roles: list[RoleDetails] = Field(default=[])


@router.post(
    "/add", status_code=status.HTTP_201_CREATED, response_model=RoleDetails
)
@authorize(roles=["admin", "superuser"])
async def add_role(
    role: RoleDetails,
    authorization: str = Depends(oauth2_scheme),
    role_service: RoleService = Depends(get_role_service),
):
    try:
        new_role = await role_service.add(
            name=role.name, description=role.description
        )
    except RoleExists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Role exists"
        )
    return RoleDetails.model_validate(new_role)


@router.delete("/delete", status_code=status.HTTP_200_OK)
@authorize(roles=["admin", "superuser"])
async def delete_role(
    form: RoleForm,
    authorization: str = Depends(oauth2_scheme),
    role_service: RoleService = Depends(get_role_service),
):
    try:
        await role_service.delete(form.id)
    except RoleNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )


@router.patch("/update", response_model=RoleDetails)
@authorize(roles=["admin", "superuser"])
async def update_role(
    form: RoleForm,
    authorization: str = Depends(oauth2_scheme),
    role_service: RoleService = Depends(get_role_service),
):
    try:
        role = await role_service.update(form.id, form.name, form.description)
    except RoleNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    return RoleDetails.model_validate(role)


@router.get("/all", response_model=list[RoleDetails])
@authorize(roles=["admin", "superuser"])
async def get_all(
    authorization: str = Depends(oauth2_scheme),
    role_service: RoleService = Depends(get_role_service),
):
    roles = await role_service.get_all()
    return [RoleDetails.model_validate(role) for role in roles]


@router.patch("/update-user", response_model=UserDetails)
@authorize(roles=["admin", "superuser"])
async def update_roles(
    user: UserForm,
    roles: list[RoleForm],
    authorization: str = Depends(oauth2_scheme),
    role_service: RoleService = Depends(get_role_service),
    user_service: UserService = Depends(get_user_service),
):
    role_ids = [i.id for i in roles]
    new_roles = await role_service.get_roles_by_ids(role_ids)
    user = await user_service.update_roles(user.id, new_roles)
    return UserDetails.model_validate(user)
