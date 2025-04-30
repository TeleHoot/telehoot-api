from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src import core
from src.app import schemas
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/quizzes", tags=["quizzes"])
settings = core.config.get_settings()

FiltersQuery = Annotated[schemas.quizzes.Filters, Depends()]
SortingQuery = Annotated[schemas.quizzes.SortParams, Depends()]


@router.post(
    "/",
    response_model=schemas.quizzes.Read,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencies.get_active_user)],
)
async def create_quiz(
    quiz_data: schemas.quizzes.Create,
    uow: dependencies.PostgresUOW,
    quizzes_service: dependencies.QuizzesService,
):
    return await quizzes_service.create(uow, quiz_data)


@router.get(
    "/",
    response_model=list[schemas.quizzes.Read],
    dependencies=[Depends(dependencies.get_active_user)],
)
async def get_quizzes(
    uow: dependencies.PostgresUOW,
    quizzes_service: dependencies.QuizzesService,
    filters: FiltersQuery,
    sorting: SortingQuery,
    pagination: dependencies.PaginationQuery,
):
    return await quizzes_service.read_many(uow, filters, sorting, pagination)


@router.get(
    "/{quiz_id}",
    response_model=schemas.quizzes.Read,
    dependencies=[Depends(dependencies.get_active_user)],
)
async def get_quiz(
    quiz_id: UUID,
    uow: dependencies.PostgresUOW,
    quizzes_service: dependencies.QuizzesService,
):
    return await quizzes_service.read_by_id(uow=uow, entity_id=quiz_id)


@router.patch(
    "/{quiz_id}",
    response_model=schemas.quizzes.Read,
    dependencies=[Depends(dependencies.get_active_user)],
)
async def update_quiz(
    quiz_id: UUID,
    quiz_data: schemas.quizzes.Update,
    uow: dependencies.PostgresUOW,
    quizzes_service: dependencies.QuizzesService,
):
    return await quizzes_service.update_by_id(
        uow=uow,
        entity_id=quiz_id,
        update_schema=quiz_data,
    )


@router.delete(
    "/{quiz_id}",
    dependencies=[Depends(dependencies.get_active_user)],
)
async def delete_quiz(
    quiz_id: UUID,
    uow: dependencies.PostgresUOW,
    quizzes_service: dependencies.QuizzesService,
):
    return {
        "is_success": await quizzes_service.delete_by_id(
            uow=uow,
            entity_id=quiz_id,
        )
    }
