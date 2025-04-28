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


@router.get(
    "/{user_id}",
    dependencies=[Depends(dependencies.get_active_user)],
    response_model=schemas.users.Read,
)
async def get_user(
    user_id: UUID, uow: dependencies.PostgresUOW, users_service: dependencies.UsersService
):
    return await users_service.read_by_id(uow, user_id)
