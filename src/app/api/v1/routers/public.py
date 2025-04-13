from fastapi import APIRouter

from src.app import schemas
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/healthcheck")
async def healthcheck():
    return 1


@router.post("/register", response_model=schemas.users.Read)
async def register(
    user_create: schemas.users.Create,
    users_service: dependencies.UsersService,
    session: dependencies.DBSession,
):
    return await users_service.create(session, user_create)
