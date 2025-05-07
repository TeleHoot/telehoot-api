from fastapi import WebSocket

from src.app.api import dependencies


@dependencies.websocket.manager.router.on("subscribe")
async def handle_subscribe(websocket: WebSocket, connection_id: str, data: dict):
    channel = data.get("channel")
    if channel:
        await dependencies.websocket.manager.subscribe_to_channel(connection_id, channel)
        await websocket.send_json({"status": f"Subscribed to {channel}"})
    else:
        await websocket.send_json({"error": "Channel not specified"})


@dependencies.websocket.manager.router.on("message")
async def handle_message(websocket: WebSocket, connection_id: str, data: dict):
    channel = data.get("channel")
    message = data.get("message")
    if channel and message:
        await dependencies.websocket.manager.broadcast_to_channel(
            channel, {"from": connection_id, "message": message}
        )
    else:
        await websocket.send_json({"error": "Channel or message not specified"})
