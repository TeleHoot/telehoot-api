from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, status

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
    quiz: dependencies.paths.CurrentQuiz,
    uow: dependencies.uow.Full,
    sessions_service: dependencies.services.Sessions,
):
    return await sessions_service.create(
        uow,
        schemas.sessions.Create(),
        additional_data={
            "quiz_id": quiz.id,
        },
    )


@router.get(
    "",
    response_model=list[schemas.sessions.Read],
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
    if str(session.quiz_id) != str(quiz.id):
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
    quiz: dependencies.paths.CurrentQuiz,
    session_id: UUID,
    session_data: schemas.sessions.Update,
    uow: dependencies.uow.Full,
    sessions_service: dependencies.services.Sessions,
):
    session = await sessions_service.read_by_id(uow, session_id)
    if str(session.quiz_id) != str(quiz.id):
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
    quiz: dependencies.paths.CurrentQuiz,
    session_id: UUID,
    uow: dependencies.uow.Full,
    sessions_service: dependencies.services.Sessions,
):
    session = await sessions_service.read_by_id(uow, session_id)
    if str(session.quiz_id) != str(quiz.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found for this quiz"
        )

    return {
        "is_success": await sessions_service.delete_by_id(
            uow,
            session_id,
        )
    }


@router.websocket("/{session_id}")
async def handle_session(
    websocket: WebSocket,
    quiz: dependencies.paths.CurrentQuizWs,
    session_id: UUID,
    uow: dependencies.uow.Full,
    sessions_service: dependencies.services.Sessions,
    current_user: dependencies.permissions.WsUser,
):
    await websocket.accept()

    session = await sessions_service.read_by_id(uow, session_id)
    if str(session.quiz.id) != str(quiz.id):
        await websocket.send_json({"error": "Session not found for this quiz"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)

    connection_id = await dependencies.websocket.manager.accept_connection(
        websocket, current_user.id
    )
    await dependencies.websocket.manager.handle_client(
        websocket, uow, connection_id, session_id, current_user
    )
