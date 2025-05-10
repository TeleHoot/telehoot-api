from uuid import UUID

from fastapi import WebSocket, status

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

    event = schemas.sessions.UserJoinedEvent.model_validate(data)

    session = await sessions_service.read_by_id(uow, session_id)
    if session.status != models.session.SessionStatus.WAITING:
        await websocket.send_json({"error": "Session must be in WAITING status"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)

    await participants_service.create(
        uow,
        schemas.participants.Create(
            user_id=user.id, role=event.role, session_nickname=event.username
        ),
        additional_data={
            "session_id": session_id,
        },
    )
    await dependencies.websocket.manager.subscribe_to_channel(user.id, str(session_id))
    await dependencies.websocket.manager.broadcast_event_to_channel(str(session_id), event)
