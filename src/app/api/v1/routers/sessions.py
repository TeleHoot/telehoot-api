from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src import core
from src.app import models, schemas
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
)
async def create_session(
    quiz: dependencies.paths.CurrentQuiz,
    uow: dependencies.uow.Full,
    sessions_service: dependencies.services.Sessions,
    participants_service: dependencies.services.Participants,
    host: dependencies.permissions.OrganizationEditor,
):
    session = await sessions_service.create(
        uow,
        schemas.sessions.Create(),
        additional_data={
            "quiz_id": quiz.id,
        },
    )

    await participants_service.create(
        uow,
        schemas.participants.Create(
            session_nickname=host.telegram_username, role=models.ParticipantRole.HOST
        ),
        additional_data={"session_id": session.id, "user_id": host.id},
    )

    return await sessions_service.read_by_id(uow, session.id)


@router.get(
    "",
    response_model=list[schemas.sessions.ReadMany],
    dependencies=[Depends(dependencies.paths.get_validated_quiz)],
)
async def get_sessions(
    uow: dependencies.uow.Full,
    sessions_service: dependencies.services.Sessions,
    filters: FiltersQuery,
    sorting: SortingQuery,
    pagination: dependencies.queries.Pagination,
    current_user: dependencies.permissions.ActiveUser,
):
    return await sessions_service.read_many(
        uow, filters, sorting, pagination, include_deleted=current_user.is_admin
    )


@router.get(
    "/{session_id}",
    response_model=schemas.sessions.Read,
)
async def get_session(
    quiz: dependencies.paths.CurrentQuiz,
    session_id: UUID,
    uow: dependencies.uow.Full,
    sessions_service: dependencies.services.Sessions,
    current_user: dependencies.permissions.ActiveUser,
):
    session = await sessions_service.read_by_id(
        uow, session_id, include_deleted=current_user.is_admin
    )
    if session.quiz.id != quiz.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found for this quiz"
        )

    return session


@router.patch(
    "/{session_id}",
    response_model=schemas.sessions.Read,
    dependencies=[Depends(dependencies.permissions.get_org_presenter)],
)
async def update_session(
    quiz: dependencies.paths.CurrentQuiz,
    session_id: UUID,
    session_data: schemas.sessions.Update,
    uow: dependencies.uow.Full,
    sessions_service: dependencies.services.Sessions,
):
    session = await sessions_service.read_by_id(uow, session_id)
    if session.quiz.id != quiz.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found for this quiz"
        )

    return await sessions_service.update_by_id(
        uow,
        session_id,
        session_data,
    )


@router.delete("/{session_id}", dependencies=[Depends(dependencies.permissions.get_org_presenter)])
async def delete_session(
    quiz: dependencies.paths.CurrentQuiz,
    session_id: UUID,
    uow: dependencies.uow.Full,
    sessions_service: dependencies.services.Sessions,
):
    session = await sessions_service.read_by_id(uow, session_id)
    if session.quiz.id != quiz.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found for this quiz"
        )

    return {
        "is_success": await sessions_service.delete_by_id(
            uow,
            session_id,
        )
    }


@router.get(
    "/{session_id}/results",
    response_model=list[schemas.sessions.SessionResult],
)
async def get_session_results(
    quiz: dependencies.paths.CurrentQuiz,
    session_id: UUID,
    uow: dependencies.uow.Full,
    sessions_service: dependencies.services.Sessions,
):
    session = await sessions_service.read_by_id(uow, session_id)
    if session.quiz.id != quiz.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found for this quiz",
        )

    return await sessions_service.get_session_results(uow, session)


@router.get(
    "/{session_id}/export", dependencies=[Depends(dependencies.permissions.get_org_presenter)]
)
async def export_session_results(
    quiz: dependencies.paths.CurrentQuiz,
    session_id: UUID,
    uow: dependencies.uow.Full,
    sessions_service: dependencies.services.Sessions,
    questions_service: dependencies.services.Questions,
):
    session = await sessions_service.read_by_id(uow, session_id)
    if session.quiz.id != quiz.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found for this quiz",
        )

    excel_file = await sessions_service.export_session_results(uow, session, questions_service)

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=results_{session_id}.xlsx"},
    )
