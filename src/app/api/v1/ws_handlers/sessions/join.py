from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect, status

from src import core
from src.app import api, models, schemas, services

ws_manager = core.websockets.get_websocket_manager()


@ws_manager.router.on(schemas.sessions.SessionEventType.JOIN)
async def handle_join(
    websocket: WebSocket,
    connection_id: UUID,
    session_id: UUID,
    data: dict,
    user: schemas.users.Read,
):
    sessions_service = services.Sessions()
    participants_service = services.Participants()

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

        participant = await participants_service.read_many(
            uow, filters=schemas.participants.Filters(user_id=user.id, session_id=session_id)
        )

        if not participant:
            try:
                participant = await participants_service.create(
                    uow,
                    schemas.participants.Create(
                        user_id=user.id,
                        session_nickname=data["username"] if data["username"] else user.username,
                    ),
                    additional_data={
                        "session_id": session_id,
                    },
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
        else:
            participant = participant[0]
            participants_service.update_by_id(
                uow,
                participant.id,
                schemas.participants.Update(
                    session_nickname=data["username"] if data["username"] else user.username
                ),
            )

        event = schemas.sessions.UserJoinedEvent(
            user_id=user.id,
            participant_id=participant.id,
            username=data["username"] if data["username"] else user.username,
            photo_url=user.photo_url,
            role=participant.role,
        )

        await ws_manager.subscribe_to_channel(user.id, str(session_id))
        await ws_manager.broadcast_event_to_channel(str(session_id), event)
