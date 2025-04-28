from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, status

from src import core
from src.app import schemas
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/questions", tags=["questions"])
settings = core.config.get_settings()


@router.post(
    "/",
    response_model=schemas.questions.Read,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencies.get_active_user)],
)
async def create_question(
    entity: schemas.questions.Create,
    uow: dependencies.MongoUOW,
    service: dependencies.QuestionsService,
):
    return await service.create(uow, entity)


@router.get(
    "/",
    response_model=list[schemas.questions.Read],
    dependencies=[Depends(dependencies.get_active_user)],
)
async def get_questions(
    uow: dependencies.MongoUOW,
    service: dependencies.QuestionsService,
    page: int = 1,
    limit: int = 10,
):
    return await service.read_many(uow, page, limit)


@router.get(
    "/{entity_id}",
    response_model=schemas.questions.Read,
    dependencies=[Depends(dependencies.get_active_user)],
)
async def get_question(
    entity_id: PydanticObjectId,
    uow: dependencies.MongoUOW,
    service: dependencies.QuestionsService,
):
    return await service.read_by_id(uow, entity_id)


@router.patch(
    "/{entity_id}",
    response_model=schemas.questions.Read,
    dependencies=[Depends(dependencies.get_active_user)],
)
async def update_question(
    entity_id: PydanticObjectId,
    entity: schemas.questions.Update,
    uow: dependencies.MongoUOW,
    service: dependencies.QuestionsService,
):
    return await service.update_by_id(
        uow=uow,
        entity_id=entity_id,
        update_schema=entity,
    )


@router.delete(
    "/{entity_id}",
    dependencies=[Depends(dependencies.get_active_user)],
)
async def delete_membership(
    entity_id: PydanticObjectId,
    uow: dependencies.MongoUOW,
    service: dependencies.QuestionsService,
):
    return {"is_success": await service.delete_by_id(uow, entity_id)}
