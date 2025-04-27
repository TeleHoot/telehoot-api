from uuid import UUID

from fastapi import APIRouter, Depends

from src.app import schemas
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(dependencies.get_active_user)],
    response_model=list[schemas.users.Read],
)
async def get_users(
    uow: dependencies.PostgresUOW,
    users_service: dependencies.UsersService,
    filter_query: dependencies.PageLimitQuery,
):
    return await users_service.read_many(uow, filter_query.page, filter_query.limit)


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
    sort_query: dependencies.OrganizationsSortQuery,
):
    memberships = await memberships_service.read_many(
        uow,
        user_id=current_user.id,
        organization_id=None,
        page=sort_query.page,
        limit=sort_query.limit,
    )

    return [membership.organization for membership in memberships]


@router.get(
    "/me/memberships",
    response_model=list[schemas.memberships.Read],
)
async def get_my_memberships(
    uow: dependencies.PostgresUOW,
    memberships_service: dependencies.MembershipsService,
    sort_query: dependencies.OrganizationsSortQuery,
    current_user: dependencies.ActiveUser,
):
    return await memberships_service.read_many(
        uow, None, current_user.id, sort_query.page, sort_query.limit
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
