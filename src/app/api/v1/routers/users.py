from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from src.app import schemas
from src.app.api import dependencies

router = APIRouter(prefix="/users", tags=["users"])

FiltersQuery = Annotated[schemas.users.Filters, Depends()]
SortingQuery = Annotated[schemas.users.SortParams, Depends()]


@router.get(
    "/",
    dependencies=[Depends(dependencies.permissions.get_active_user)],
    response_model=list[schemas.users.Read],
)
async def get_users(
    uow: dependencies.uow.Postgres,
    users_service: dependencies.services.Users,
    filters: FiltersQuery,
    sorting: SortingQuery,
    pagination: dependencies.queries.Pagination,
):
    return await users_service.read_many(uow, filters, sorting, pagination)


@router.get("/me/")
async def get_me(current_user: dependencies.permissions.ActiveUser):
    return current_user


@router.get(
    "/me/organizations/",
    response_model=list[schemas.organizations.Read],
)
async def get_my_organizations(
    uow: dependencies.uow.Postgres,
    memberships_service: dependencies.services.Memberships,
    organizations_service: dependencies.services.Organizations,
    current_user: dependencies.permissions.ActiveUser,
    pagination: dependencies.queries.Pagination,
):
    memberships = await memberships_service.read_many(
        uow, filters=schemas.memberships.Filters(user_id=current_user.id), pagination=pagination
    )

    return [
        await organizations_service.read_by_id(uow, membership.organization.id)
        for membership in memberships
    ]


@router.get(
    "/me/memberships/",
    response_model=list[schemas.memberships.Read],
)
async def get_my_memberships(
    uow: dependencies.uow.Postgres,
    memberships_service: dependencies.services.Memberships,
    current_user: dependencies.permissions.ActiveUser,
    pagination: dependencies.queries.Pagination,
):
    return await memberships_service.read_many(
        uow, filters=schemas.memberships.Filters(user_id=current_user.id), pagination=pagination
    )


@router.get(
    "/{user_id}/",
    dependencies=[Depends(dependencies.permissions.get_active_user)],
    response_model=schemas.users.Read,
)
async def get_user(
    user_id: UUID, uow: dependencies.uow.Postgres, users_service: dependencies.services.Users
):
    return await users_service.read_by_id(uow, user_id)
