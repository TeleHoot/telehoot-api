import logging
from collections.abc import Callable
from typing import Any, TypeVar
from uuid import UUID

from fastapi import WebSocket
from pydantic import BaseModel

from src.core import utils
from src.core.config import get_settings

settings = get_settings()
TEvent = TypeVar("TEvent", bound=BaseModel)


@utils.decorators.Singleton
class Router:
    def __init__(self):
        self.handlers: dict[str, Callable] = {}
        self.logger = logging.getLogger(f"websocket.{self.__class__.__name__.lower()}")

    def on(self, message_type: str):
        def decorator(handler: Callable):
            self.handlers[message_type] = handler
            self.logger.info("Registered handler for message type: %s", message_type)
            return handler

        return decorator

    async def handle(
        self,
        websocket: WebSocket,
        connection_id: UUID,
        session_id: UUID,
        data: dict[str, Any],
        user: BaseModel,
    ):
        self.logger.debug("Handling message for %s: %s", connection_id, data)
        if not isinstance(data, dict):
            self.logger.warning("Invalid message format from %s", connection_id)
            await websocket.send_json({"error": "Invalid message format"})
            return

        message_type = data.get("type")
        handler = self.handlers.get(message_type)  # type: ignore[valid-type]
        if handler:
            self.logger.info("Processing message type %s for %s", message_type, connection_id)
            await handler(websocket, connection_id, session_id, data, user)
        else:
            self.logger.warning("Unknown message type %s from %s", message_type, connection_id)
            await websocket.send_json({
                "error": "Unknown message type",
                "received_type": message_type,
            })


def get_websocket_router() -> Router:
    return Router()
