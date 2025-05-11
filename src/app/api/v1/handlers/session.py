from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError

from src import core
from src.app import models, schemas, services
from src.app.api import dependencies


@dependencies.websocket.manager.router.on(schemas.sessions.SessionEventType.JOIN)
async def handle_join(
    websocket: WebSocket,
    uow: core.UnitOfWork,
    connection_id: UUID,
    session_id: UUID,
    data: dict,
    user: schemas.users.Read,
):
    sessions_service = services.Sessions()
    participants_service = services.Participants()

    try:
        event = schemas.sessions.UserJoinedEvent.model_validate(data)

        session = await sessions_service.read_by_id(uow, session_id)
        if session.status != models.session.SessionStatus.WAITING:
            await dependencies.websocket.manager.send_event_to_connection(
                connection_id,
                schemas.sessions.ErrorEvent(
                    error_code="invalid_session_status",
                    message="Session must be in WAITING status",
                    code=status.WS_1008_POLICY_VIOLATION,
                ),
            )
            raise WebSocketDisconnect  # noqa: TRY301

        participant = await participants_service.create(
            uow,
            schemas.participants.Create(
                user_id=user.id, role=event.role, session_nickname=event.username
            ),
            additional_data={
                "session_id": session_id,
            },
        )
        event.participant_id = participant.id

        await dependencies.websocket.manager.subscribe_to_channel(user.id, str(session_id))
        await dependencies.websocket.manager.broadcast_event_to_channel(str(session_id), event)
    except core.services.exceptions.EntityNotFoundError as e:
        await dependencies.websocket.manager.send_event_to_connection(
            connection_id,
            schemas.sessions.ErrorEvent(
                error_code="entity_not_found",
                message="Session not found",
                code=status.WS_1003_UNSUPPORTED_DATA,
            ),
        )
        raise WebSocketDisconnect from e
    except ValidationError as e:
        await dependencies.websocket.manager.send_event_to_connection(
            connection_id,
            schemas.sessions.ErrorEvent(
                error_code="invalid_schema", message=str(e), code=status.WS_1003_UNSUPPORTED_DATA
            ),
        )
        raise WebSocketDisconnect from e
    except Exception as e:
        await dependencies.websocket.manager.send_event_to_connection(
            connection_id,
            schemas.sessions.ErrorEvent(
                error_code="internal_server_error",
                message=str(e),
                code=status.WS_1011_INTERNAL_ERROR,
            ),
        )
        raise WebSocketDisconnect from e


@dependencies.websocket.manager.router.on(schemas.sessions.SessionEventType.LEAVE)
async def handle_leave(
    websocket: WebSocket,
    uow: core.UnitOfWork,
    connection_id: UUID,
    session_id: UUID,
    data: dict,
    user: schemas.users.Read,
):
    participants_service = services.Participants()

    try:
        event = schemas.sessions.UserLeftEvent.model_validate(data)
        await participants_service.delete_by_id(uow, event.participant_id)
    except core.services.exceptions.EntityNotFoundError as e:
        await dependencies.websocket.manager.send_event_to_connection(
            connection_id,
            schemas.sessions.ErrorEvent(
                error_code="entity_not_found",
                message="Provided participant not found",
                code=status.WS_1003_UNSUPPORTED_DATA,
            ),
        )
        raise WebSocketDisconnect from e
    except ValidationError as e:
        await dependencies.websocket.manager.send_event_to_connection(
            connection_id,
            schemas.sessions.ErrorEvent(
                error_code="invalid_schema", message=str(e), code=status.WS_1003_UNSUPPORTED_DATA
            ),
        )
        raise WebSocketDisconnect from e
    except Exception as e:
        await dependencies.websocket.manager.send_event_to_connection(
            connection_id,
            schemas.sessions.ErrorEvent(
                error_code="internal_server_error",
                message=str(e),
                code=status.WS_1011_INTERNAL_ERROR,
            ),
        )
        raise WebSocketDisconnect from e

    await dependencies.websocket.manager.broadcast_event_to_channel(str(session_id), event)
    await dependencies.websocket.manager.unsubscribe_from_channel(user.id, str(session_id))
    raise WebSocketDisconnect
