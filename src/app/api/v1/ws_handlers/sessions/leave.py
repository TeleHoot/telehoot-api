from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError

from src import core
from src.app import schemas, services

ws_manager = core.websockets.get_websocket_manager()


@ws_manager.router.on(schemas.sessions.SessionEventType.LEAVE)
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
    except ValidationError as e:
        await ws_manager.send_event_to_connection(
            connection_id,
            schemas.sessions.ErrorEvent(
                error_code="invalid_schema", message=str(e), code=status.WS_1003_UNSUPPORTED_DATA
            ),
        )
        raise WebSocketDisconnect from e

    try:
        await participants_service.delete_by_id(uow, event.participant_id)
    except core.services.exceptions.EntityNotFoundError as e:
        await ws_manager.send_event_to_connection(
            connection_id,
            schemas.sessions.ErrorEvent(
                error_code="entity_not_found",
                message="Provided participant not found",
                code=status.WS_1003_UNSUPPORTED_DATA,
            ),
        )
        raise WebSocketDisconnect from e
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

    await ws_manager.broadcast_event_to_channel(str(session_id), event)
    await ws_manager.unsubscribe_from_channel(user.id, str(session_id))
    raise WebSocketDisconnect
