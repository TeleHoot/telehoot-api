from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from src.app import schemas
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/users", tags=["users"])

FiltersQuery = Annotated[schemas.users.Filters, Depends()]
SortingQuery = Annotated[schemas.users.SortParams, Depends()]


@router.get(
    "/",
    dependencies=[Depends(dependencies.get_active_user)],
    response_model=list[schemas.users.Read],
)
async def get_users(
    uow: dependencies.PostgresUOW,
    users_service: dependencies.UsersService,
    filters: FiltersQuery,
    sorting: SortingQuery,
    pagination: dependencies.PaginationQuery,
):
    return await users_service.read_many(uow, filters, sorting, pagination)


@router.get("/me")
async def get_me(current_user: dependencies.ActiveUser):
    return current_user


@router.get(
    "/me/organizations",
    response_model=list[schemas.organizations.Read],
)
async def get_my_organizations(
    uow: dependencies.PostgresUOW,
    memberships_service: dependencies.MembershipsService,
    current_user: dependencies.ActiveUser,
    pagination: dependencies.PaginationQuery,
):
    memberships = await memberships_service.read_many(
        uow, filters=schemas.memberships.Filters(user_id=current_user.id), pagination=pagination
    )

    return [membership.organization for membership in memberships]


@router.get(
    "/me/memberships",
    response_model=list[schemas.memberships.Read],
)
async def get_my_memberships(
    uow: dependencies.PostgresUOW,
    memberships_service: dependencies.MembershipsService,
    current_user: dependencies.ActiveUser,
    pagination: dependencies.PaginationQuery,
):
    return await memberships_service.read_many(
        uow, filters=schemas.memberships.Filters(user_id=current_user.id), pagination=pagination
    )


@router.get(
    "/{user_id}",
    dependencies=[Depends(dependencies.get_active_user)],
    response_model=schemas.users.Read,
)
async def get_user(
    user_id: UUID, uow: dependencies.PostgresUOW, users_service: dependencies.UsersService
):
    return await users_service.read_by_id(uow, user_id)
