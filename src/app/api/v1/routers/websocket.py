from fastapi import APIRouter, WebSocket
from src.app.services.websocket_service import websocket_service
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/session/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    current_user: dependencies.WsUser
):
    await websocket_service.handle_connection(
        websocket=websocket,
        session_id=session_id,
        current_user=current_user
    )
