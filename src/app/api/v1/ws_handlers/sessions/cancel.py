from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect, status

from src import core
from src.app import api, models, schemas, services

ws_manager = core.websockets.get_websocket_manager()


@ws_manager.router.on(schemas.sessions.SessionEventType.CANCEL)
async def handle_cancel(
    websocket: WebSocket,
    connection_id: UUID,
    session_id: UUID,
    data: dict,
    user: schemas.users.Read,
):
    sessions_service = services.Sessions()

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

        if str(session.status).lower() not in {
            str(models.session.SessionStatus.ACTIVE).lower(),
            str(models.session.SessionStatus.WAITING).lower(),
        }:
            await ws_manager.send_event_to_connection(
                connection_id,
                schemas.sessions.ErrorEvent(
                    error_code="invalid_session_status",
                    message="Session must be in ACTIVE or WAITING status",
                    code=status.WS_1008_POLICY_VIOLATION,
                ),
            )
            raise WebSocketDisconnect

        try:
            await sessions_service.update_by_id(
                uow,
                session_id,
                schemas.sessions.Update(status=models.session.SessionStatus.CANCELED),
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

        event = schemas.sessions.SessionCanceledEvent()

        await ws_manager.broadcast_event_to_channel(str(session_id), event)
        await ws_manager.unsubscribe_from_channel(user.id, str(session_id))
    raise WebSocketDisconnect
