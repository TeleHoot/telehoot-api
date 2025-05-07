from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src import core
from src.app import schemas
from src.app.api import dependencies

router = APIRouter(
    prefix="/organizations/{organization_id}/quizzes/{quiz_id}/sessions", tags=["sessions"]
)
settings = core.config.get_settings()

FiltersQuery = Annotated[schemas.sessions.Filters, Depends()]
SortingQuery = Annotated[schemas.sessions.SortParams, Depends()]


@router.post(
    "",
    response_model=schemas.sessions.Read,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencies.permissions.get_active_user)],
)
async def create_session(
    organization_id: UUID,
    quiz_id: UUID,
    uow: dependencies.uow.Full,
    sessions_service: dependencies.services.Sessions,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
):
    await org_service.read_by_id(uow, organization_id)
    quiz = await quizzes_service.read_by_id(uow, quiz_id)
    if str(quiz.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quiz does not belong to this organization",
        )

    return await sessions_service.create(
        uow,
        schemas.sessions.Create(),
        additional_data={
            "quiz_id": quiz_id,
        },
    )


@router.get(
    "",
    response_model=list[schemas.sessions.Read],
)
async def get_sessions(
    organization_id: UUID,
    quiz_id: UUID,
    uow: dependencies.uow.Full,
    sessions_service: dependencies.services.Sessions,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
    filters: FiltersQuery,
    sorting: SortingQuery,
    pagination: dependencies.queries.Pagination,
    current_user: dependencies.permissions.ActiveUser,
):
    await org_service.read_by_id(uow, organization_id)
    quiz = await quizzes_service.read_by_id(uow, quiz_id)
    if str(quiz.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quiz does not belong to this organization",
        )

    return await sessions_service.read_many(
        uow, filters, sorting, pagination, include_deleted=current_user.is_admin
    )


@router.get(
    "/{session_id}",
    response_model=schemas.sessions.Read,
)
async def get_session(
    organization_id: UUID,
    quiz_id: UUID,
    session_id: UUID,
    uow: dependencies.uow.Full,
    sessions_service: dependencies.services.Sessions,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
    current_user: dependencies.permissions.ActiveUser,
):
    await org_service.read_by_id(uow, organization_id)
    quiz = await quizzes_service.read_by_id(uow, quiz_id, include_deleted=current_user.is_admin)
    if str(quiz.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quiz does not belong to this organization",
        )

    session = await sessions_service.read_by_id(
        uow, session_id, include_deleted=current_user.is_admin
    )
    if str(session.quiz_id) != str(quiz_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found for this quiz"
        )

    return session


@router.patch(
    "/{session_id}",
    response_model=schemas.sessions.Read,
    dependencies=[Depends(dependencies.permissions.get_active_user)],
)
async def update_session(
    organization_id: UUID,
    quiz_id: UUID,
    session_id: UUID,
    session_data: schemas.sessions.Update,
    uow: dependencies.uow.Full,
    sessions_service: dependencies.services.Sessions,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
):
    await org_service.read_by_id(uow, organization_id)
    quiz = await quizzes_service.read_by_id(uow, quiz_id)
    if str(quiz.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quiz does not belong to this organization",
        )

    session = await sessions_service.read_by_id(uow, session_id)
    if str(session.quiz_id) != str(quiz_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found for this quiz"
        )

    return await sessions_service.update_by_id(
        uow,
        session_id,
        session_data,
    )


@router.delete(
    "/{session_id}",
    dependencies=[Depends(dependencies.permissions.get_active_user)],
)
async def delete_session(
    organization_id: UUID,
    quiz_id: UUID,
    session_id: UUID,
    uow: dependencies.uow.Full,
    sessions_service: dependencies.services.Sessions,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
):
    await org_service.read_by_id(uow, organization_id)
    quiz = await quizzes_service.read_by_id(uow, quiz_id)
    if str(quiz.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quiz does not belong to this organization",
        )

    session = await sessions_service.read_by_id(uow, session_id)
    if str(session.quiz_id) != str(quiz_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found for this quiz"
        )

    return {
        "is_success": await sessions_service.delete_by_id(
            uow,
            session_id,
        )
    }
