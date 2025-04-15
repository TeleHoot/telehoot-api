from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from src.app import schemas
from src.app.api.v1 import dependencies
from src.app.models import User

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/healthcheck")
async def healthcheck():
    return 1


@router.post("/register", response_model=schemas.users.Read)
async def register(
    user_create: schemas.users.Create,
    users_service: dependencies.UsersService,
    uow: dependencies.PostgresUOW,
):
    return await users_service.create(uow, user_create)


class TransferRequest(BaseModel):
    from_user1_name: str
    from_user2_name: str
    amount: float = Field(gt=0)


@router.post("/double-money-take")
async def double_money_take(
    request: TransferRequest,
    uow: dependencies.PostgresUOW,
):
    session = uow.postgres_session

    from_user1 = await session.scalar(select(User).where(User.name == request.from_user1_name))
    from_user2 = await session.scalar(select(User).where(User.name == request.from_user2_name))

    if not from_user1 or not from_user2:
        raise HTTPException(status_code=404, detail="User not found")
    if from_user1.balance < request.amount:
        raise HTTPException(status_code=400, detail="No money 1")
    from_user1.balance -= request.amount

    await session.flush()

    if from_user2.balance < request.amount:
        raise HTTPException(status_code=400, detail="No money 1")
    from_user2.balance -= request.amount

    return {
        "message": "Transfer successful",
        "new_balances": {"from_user1": from_user1.balance, "from_user2": from_user2.balance},
    }
