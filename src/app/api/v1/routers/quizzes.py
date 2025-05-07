from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src import core
from src.app import schemas
from src.app.api import dependencies

router = APIRouter(prefix="/organizations/{organization_id}/quizzes", tags=["quizzes"])
settings = core.config.get_settings()

FiltersQuery = Annotated[schemas.quizzes.Filters, Depends()]
SortingQuery = Annotated[schemas.quizzes.SortParams, Depends()]


@router.post(
    "",
    response_model=schemas.quizzes.Read,
    status_code=status.HTTP_201_CREATED,
)
async def create_quiz(
    organization_id: UUID,
    quiz_data: schemas.quizzes.Create,
    uow: dependencies.uow.Full,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
    current_user: dependencies.permissions.ActiveUser,
):
    await org_service.read_by_id(uow, organization_id)
    return await quizzes_service.create(
        uow,
        quiz_data,
        additional_data={
            "author_id": current_user.id,
            "organization_id": organization_id,
        },
    )


@router.get(
    "",
    response_model=list[schemas.quizzes.Read],
)
async def get_quizzes(
    organization_id: UUID,
    uow: dependencies.uow.Full,
    quizzes_service: dependencies.services.Quizzes,
    filters: FiltersQuery,
    sorting: SortingQuery,
    pagination: dependencies.queries.Pagination,
    current_user: dependencies.permissions.ActiveUser,
):
    return await quizzes_service.read_many(
        uow, filters, sorting, pagination, include_deleted=current_user.is_admin
    )


@router.get(
    "/{quiz_id}",
    response_model=schemas.quizzes.Read,
)
async def get_quiz(
    organization_id: UUID,
    quiz_id: UUID,
    uow: dependencies.uow.Full,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
    current_user: dependencies.permissions.ActiveUser,
):
    await org_service.read_by_id(uow, organization_id, include_deleted=current_user.is_admin)
    return await quizzes_service.read_by_id(uow, quiz_id, include_deleted=current_user.is_admin)


@router.patch(
    "/{quiz_id}",
    response_model=schemas.quizzes.Read,
    dependencies=[Depends(dependencies.permissions.get_active_user)],
)
async def update_quiz(
    organization_id: UUID,
    quiz_id: UUID,
    quiz_data: schemas.quizzes.Update,
    uow: dependencies.uow.Full,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
):
    await org_service.read_by_id(uow, organization_id)
    return await quizzes_service.update_by_id(
        uow,
        quiz_id,
        quiz_data,
    )


@router.delete(
    "/{quiz_id}",
    dependencies=[Depends(dependencies.permissions.get_active_user)],
)
async def delete_quiz(
    organization_id: UUID,
    quiz_id: UUID,
    uow: dependencies.uow.Full,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
):
    await org_service.read_by_id(uow, organization_id)
    return {
        "is_success": await quizzes_service.delete_by_id(
            uow,
            quiz_id,
        )
    }
