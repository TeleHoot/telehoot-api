from uuid import UUID

from fastapi import APIRouter, WebSocket, status
from starlette.websockets import WebSocketDisconnect

from src import core
from src.app import models, schemas
from src.app.api import dependencies

router = APIRouter()

settings = core.config.get_settings()


@router.websocket("/sessions/handle/id/{session_id}")
async def handle_session_by_id(
    websocket: WebSocket,
    session_id: UUID,
    ws_controller: dependencies.websockets.Controller,
    current_user: dependencies.permissions.WsUser,
):
    await websocket.accept()

    connection_id = await ws_controller.manager.accept_connection(websocket, current_user.id)
    await ws_controller.manager.handle_client(websocket, connection_id, session_id, current_user)


@router.websocket("/sessions/handle/join-code/{join_code}")
async def handle_session_by_join_code(
    websocket: WebSocket,
    join_code: str,
    sessions_service: dependencies.services.Sessions,
    ws_controller: dependencies.websockets.Controller,
    current_user: dependencies.permissions.WsUser,
):
    await websocket.accept()
    connection_id = await ws_controller.manager.accept_connection(websocket, current_user.id)

    uow_factory = dependencies.uow.get_uow_factory(use_postgres=True, use_mongodb=True)

    sessions = None
    async for uow in uow_factory():
        sessions = await sessions_service.read_many(
            uow,
            filters=schemas.sessions.Filters(
                join_code=join_code, status=models.session.SessionStatus.WAITING
            ),
        )

        if not sessions:
            await ws_controller.manager.send_event_to_connection(
                connection_id,
                schemas.sessions.ErrorEvent(
                    error_code="entity_not_found",
                    message="Session not found by join code",
                    code=status.WS_1003_UNSUPPORTED_DATA,
                ),
            )
            raise WebSocketDisconnect

    if sessions:
        await ws_controller.manager.handle_client(
            websocket, connection_id, sessions[0].id, current_user
        )
