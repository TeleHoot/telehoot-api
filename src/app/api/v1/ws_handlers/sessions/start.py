from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect, status

from src import core
from src.app import api, models, schemas, services

ws_manager = core.websockets.get_websocket_manager()


@ws_manager.router.on(schemas.sessions.SessionEventType.START)
async def handle_start(
    websocket: WebSocket,
    connection_id: UUID,
    session_id: UUID,
    data: dict,
    user: schemas.users.Read,
):
    sessions_service = services.Sessions()
    participants_service = services.Participants()
    questions_service = services.Questions()

    uow_factory = api.dependencies.uow.get_uow_factory(use_postgres=True, use_mongodb=True)

    async for uow in uow_factory():
        try:
            session = await sessions_service.read_by_id(uow, session_id)
        except core.services.exceptions.EntityNotFoundError as e:
            await ws_manager.send_event_to_connection(
                connection_id,
                schemas.sessions.ErrorEvent(
                    error_code="entity_not_found",
                    message="Session not found",
                    code=status.WS_1003_UNSUPPORTED_DATA,
                ),
            )
            raise WebSocketDisconnect from e

        if str(session.status).lower() != str(models.session.SessionStatus.WAITING).lower():
            await ws_manager.send_event_to_connection(
                connection_id,
                schemas.sessions.ErrorEvent(
                    error_code="invalid_session_status",
                    message="Session must be in WAITING status",
                    code=status.WS_1008_POLICY_VIOLATION,
                ),
            )
            raise WebSocketDisconnect

        participant = await participants_service.read_many(
            uow, filters=schemas.participants.Filters(user_id=user.id, session_id=session_id)
        )

        if not participant:
            await ws_manager.send_event_to_connection(
                connection_id,
                schemas.sessions.ErrorEvent(
                    error_code="entity_not_found",
                    message="Participant not found",
                    code=status.WS_1003_UNSUPPORTED_DATA,
                ),
            )
            raise WebSocketDisconnect

        participant = participant[0]

        if str(participant.role).lower() != str(models.ParticipantRole.HOST).lower():
            await ws_manager.send_event_to_connection(
                connection_id,
                schemas.sessions.ErrorEvent(
                    error_code="invalid_user_role",
                    message="To start session user must be host",
                    code=status.WS_1008_POLICY_VIOLATION,
                ),
            )
            raise WebSocketDisconnect

        try:
            await sessions_service.update_by_id(
                uow,
                session_id,
                schemas.sessions.Update(status=models.session.SessionStatus.ACTIVE),
            )

            questions = await questions_service.read_many(
                uow,
                filters=schemas.questions.Filters(quiz_id=session.quiz.id),
                sorting=schemas.questions.SortParams(sort_by=schemas.questions.SortFields.ORDER),
            )
            question = questions[0]
        except Exception as e:
            await ws_manager.send_event_to_connection(
                connection_id,
                schemas.sessions.ErrorEvent(
                    error_code="internal_server_error",
                    message=str(e),
                    code=status.WS_1011_INTERNAL_ERROR,
                ),
            )
            raise WebSocketDisconnect from e

        event = schemas.sessions.SessionStartedEvent(question=question)

        await ws_manager.broadcast_event_to_channel(str(session_id), event)
