from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect, status

from src import core
from src.app import models, schemas, services

ws_manager = core.websockets.get_websocket_manager()


@ws_manager.router.on(schemas.sessions.SessionEventType.JOIN)
async def handle_start(
    websocket: WebSocket,
    uow: core.UnitOfWork,
    connection_id: UUID,
    session_id: UUID,
    data: dict,
    user: schemas.users.Read,
):
    sessions_service = services.Sessions()
    participants_service = services.Participants()

    event = schemas.sessions.SessionStartedEvent

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

    try:
        participant = await participants_service.read_many(
            uow, user_id=user.id, session_id=session_id
        )[0]
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

    if session.status != models.session.SessionStatus.WAITING:
        await ws_manager.send_event_to_connection(
            connection_id,
            schemas.sessions.ErrorEvent(
                error_code="invalid_session_status",
                message="Session must be in WAITING status",
                code=status.WS_1008_POLICY_VIOLATION,
            ),
        )
        raise WebSocketDisconnect

    if participant.role != models.ParticipantRole.HOST:
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
        sessions_service.update_by_id(
            uow, session_id, schemas.sessions.Update(status=models.session.SessionStatus.ACTIVE)
        )
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

    await ws_manager.subscribe_to_channel(user.id, str(session_id))
    await ws_manager.broadcast_event_to_channel(str(session_id), event)
