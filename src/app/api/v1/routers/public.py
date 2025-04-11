from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel, Field
from sqlalchemy import select

from src import core
from src.app import schemas
from src.app.api.v1 import dependencies
from src.app.models import User, Question

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/healthcheck")
async def healthcheck():
    return 1




@router.post("/register", response_model=schemas.UserRead)
async def register(
    user_create: schemas.UserCreate,
    users_service: dependencies.UsersService,
    uow: Annotated[core.db.MultiDBUnitOfWork, Depends(core.db.UOWDependency())],
):
    return await users_service.create(uow, user_create)


class TransferRequest(BaseModel):
    from_user1_name: str
    from_user2_name: str
    amount: float = Field(gt=0)


@router.post("/double-money-take")
async def double_money_take(
    request: TransferRequest,
    uow: Annotated[core.db.MultiDBUnitOfWork, Depends(core.db.UOWDependency())],
):
    session = uow.get_sql_session()

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




@router.post("/questions", response_model=schemas.QuestionRead)
async def create_question(question_data: schemas.QuestionCreate):
    question = Question(**question_data.model_dump())
    await question.insert()
    return question

@router.get("/questions", response_model=list[schemas.QuestionRead])
async def get_questions(uow: core.db.MultiDBUnitOfWork = Depends(core.db.UOWDependency(use_sqlalchemy=False, use_mongodb=True)),):


    try:
        mongo_session = uow.get_mongo_session()

        return await Question.find_all(session=mongo_session).to_list()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Transaction failed: {str(e)}"
        )


@router.post("/transaction-test/{question_id}")
async def test_transaction(
        question_id: PydanticObjectId,
        uow: core.db.MultiDBUnitOfWork = Depends(core.db.UOWDependency(use_sqlalchemy=False, use_mongodb=True)),
):
    try:
        mongo_session = uow.get_mongo_session()

        # First valid update
        question = await Question.get(question_id, session=mongo_session)
        print("pudge")
        print(question)
        await question.set({"title": "Updated Title"}, session=mongo_session)

        # Second invalid update that will fail
        await question.set({"non_existing_field": "value"}, session=mongo_session)

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Transaction failed: {str(e)}"
        )

    return {"message": "Transaction completed successfully"}