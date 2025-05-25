from uuid import UUID

from fastapi import WebSocket

from src import core
from src.app import schemas

ws_manager = core.websockets.get_websocket_manager()


@ws_manager.router.on(schemas.sessions.SessionEventType.SHOW_ANSWERS)
async def handle_show_answers(
    websocket: WebSocket,
    connection_id: UUID,
    session_id: UUID,
    data: dict,
    user: schemas.users.Read,
):
    event = schemas.sessions.SessionShowedAnswersEvent()
    await ws_manager.broadcast_event_to_channel(str(session_id), event)
