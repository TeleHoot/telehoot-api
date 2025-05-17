from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src import core
from src.app import models, schemas
from src.app.api import dependencies

router = APIRouter(
    prefix="/organizations/{organization_id}/quizzes/{quiz_id}/sessions/{session_id}/participants",
    tags=["participants"],
)
settings = core.config.get_settings()

FiltersQuery = Annotated[schemas.participants.Filters, Depends()]
SortingQuery = Annotated[schemas.participants.SortParams, Depends()]


@router.post(
    "",
    response_model=schemas.participants.Read,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencies.permissions.get_active_user)],
)
async def create_participant(
    organization_id: UUID,
    quiz_id: UUID,
    session_id: UUID,
    participant_data: schemas.participants.Create,
    uow: dependencies.uow.Full,
    participants_service: dependencies.services.Participants,
    sessions_service: dependencies.services.Sessions,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
    current_user: dependencies.permissions.ActiveUser,
):
    await org_service.read_by_id(uow, organization_id)
    await quizzes_service.read_by_id(uow, quiz_id)

    session = await sessions_service.read_by_id(uow, session_id)
    if session.status != models.SessionStatus.WAITING:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="This session is no longer in WAITING status",
        )

    return await participants_service.create(
        uow,
        participant_data,
        additional_data={"session_id": session_id, "user_id": current_user.id},
    )


@router.get(
    "",
    response_model=list[schemas.participants.Read],
)
async def get_participants(
    organization_id: UUID,
    quiz_id: UUID,
    session_id: UUID,
    uow: dependencies.uow.Full,
    participants_service: dependencies.services.Participants,
    sessions_service: dependencies.services.Sessions,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
    filters: FiltersQuery,
    sorting: SortingQuery,
    pagination: dependencies.queries.Pagination,
    current_user: dependencies.permissions.ActiveUser,
):
    await org_service.read_by_id(uow, organization_id)
    await quizzes_service.read_by_id(uow, quiz_id)
    await sessions_service.read_by_id(uow, session_id)

    return await participants_service.read_many(
        uow,
        filters,
        sorting,
        pagination,
        include_deleted=current_user.is_admin,
    )


@router.get(
    "/{participant_id}",
    response_model=schemas.participants.Read,
)
async def get_participant(
    organization_id: UUID,
    quiz_id: UUID,
    session_id: UUID,
    participant_id: UUID,
    uow: dependencies.uow.Full,
    participants_service: dependencies.services.Participants,
    sessions_service: dependencies.services.Sessions,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
    current_user: dependencies.permissions.ActiveUser,
):
    await org_service.read_by_id(uow, organization_id)
    await quizzes_service.read_by_id(uow, quiz_id)
    await sessions_service.read_by_id(uow, session_id)

    return await participants_service.read_by_id(
        uow,
        participant_id,
        include_deleted=current_user.is_admin,
    )


@router.patch(
    "/{participant_id}",
    response_model=schemas.participants.Read,
    dependencies=[Depends(dependencies.permissions.get_active_user)],
)
async def update_participant(
    organization_id: UUID,
    quiz_id: UUID,
    session_id: UUID,
    participant_id: UUID,
    participant_data: schemas.participants.Update,
    uow: dependencies.uow.Full,
    participants_service: dependencies.services.Participants,
    sessions_service: dependencies.services.Sessions,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
):
    await org_service.read_by_id(uow, organization_id)
    await quizzes_service.read_by_id(uow, quiz_id)
    await sessions_service.read_by_id(uow, session_id)

    return await participants_service.update_by_id(
        uow,
        participant_id,
        participant_data,
    )


@router.delete(
    "/{participant_id}",
    dependencies=[Depends(dependencies.permissions.get_active_user)],
)
async def delete_participant(
    organization_id: UUID,
    quiz_id: UUID,
    session_id: UUID,
    participant_id: UUID,
    uow: dependencies.uow.Full,
    participants_service: dependencies.services.Participants,
    sessions_service: dependencies.services.Sessions,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
):
    await org_service.read_by_id(uow, organization_id)
    await quizzes_service.read_by_id(uow, quiz_id)
    await sessions_service.read_by_id(uow, session_id)

    return {
        "is_success": await participants_service.delete_by_id(
            uow,
            participant_id,
        )
    }
