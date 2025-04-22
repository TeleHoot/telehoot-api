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
    page: int = 1,
    limit: int = 10,
):
    return await users_service.read_many(uow, page, limit)


@router.get(
    "/{user_id}",
    dependencies=[Depends(dependencies.get_active_user)],
    response_model=schemas.users.Read,
)
async def get_user(
    user_id: UUID, uow: dependencies.PostgresUOW, users_service: dependencies.UsersService
):
    return await users_service.read_by_id(uow, user_id)
