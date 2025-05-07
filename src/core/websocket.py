import asyncio
import contextlib
import json
from collections.abc import Callable
from typing import Any
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from redis.asyncio import Redis
from redis.asyncio.client import PubSub

from src.core import utils
from src.core.config import get_settings

settings = get_settings()


@utils.decorators.Singleton
class Manager:
    def __init__(self):
        self.redis_url = settings.REDIS.URL
        self.redis: Redis | None = None
        self.local_connections: dict[str, WebSocket] = {}
        self.channel_subscriptions: dict[str, set[str]] = {}

        # Pub/sub channels
        self.connection_channel = "websocket:connections"
        self.message_channel_prefix = "websocket:messages:"

        self.pubsub: PubSub | None = None
        self._listener_task = None

        self.router = get_websocket_router()

    async def connect(self):
        """Initialize Redis connection and pub/sub"""
        self.redis = Redis.from_url(self.redis_url)
        self.pubsub = self.redis.pubsub()
        await self.pubsub.subscribe(self.connection_channel)
        self._listener_task = asyncio.create_task(self._listen_to_redis())

    async def disconnect(self):
        """Cleanup Redis connection"""
        if self._listener_task:
            self._listener_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listener_task

        if self.redis:
            await self.redis.close()

    async def _listen_to_redis(self):
        """Listen for messages from Redis pub/sub"""
        if not self.pubsub:
            return

        async for message in self.pubsub.listen():
            if message["type"] != "message":
                continue

            data = json.loads(message["data"])

            # Handle connection events
            if message["channel"] == self.connection_channel:
                if data["type"] == "disconnect":
                    connection_id = data["connection_id"]
                    if connection_id in self.local_connections:
                        await self._local_disconnect(connection_id)

            # Handle message events
            elif message["channel"].startswith(self.message_channel_prefix):
                channel = message["channel"][len(self.message_channel_prefix) :]
                await self._broadcast_to_local(channel, data["message"])

    async def accept_connection(
        self, websocket: WebSocket, connection_id: str | None = None
    ) -> str:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            connection_id: Optional custom connection ID

        Returns:
            The connection ID
        """
        connection_id = connection_id or str(uuid4())
        self.local_connections[connection_id] = websocket

        # Notify other instances about new connection
        if self.redis:
            await self.redis.publish(
                self.connection_channel,
                json.dumps({"type": "connect", "connection_id": connection_id}),
            )

        return connection_id

    async def disconnect_connection(self, connection_id: str):
        """
        Disconnect a WebSocket connection.

        Args:
            connection_id: The connection ID to disconnect
        """
        if connection_id in self.local_connections:
            await self._local_disconnect(connection_id)

        # Notify other instances about disconnection
        if self.redis:
            await self.redis.publish(
                self.connection_channel,
                json.dumps({"type": "disconnect", "connection_id": connection_id}),
            )

    async def _local_disconnect(self, connection_id: str):
        """Handle local disconnection cleanup"""
        if connection_id in self.local_connections:
            websocket = self.local_connections[connection_id]
            await websocket.close()
            del self.local_connections[connection_id]

            # Remove from all channel subscriptions
            for channel in list(self.channel_subscriptions.keys()):
                if connection_id in self.channel_subscriptions[channel]:
                    self.channel_subscriptions[channel].remove(connection_id)
                    if not self.channel_subscriptions[channel]:
                        del self.channel_subscriptions[channel]

    async def subscribe_to_channel(self, connection_id: str, channel: str):
        """
        Subscribe a connection to a channel.

        Args:
            connection_id: The connection ID
            channel: The channel to subscribe to
        """
        if connection_id not in self.local_connections:
            return

        if not self.pubsub:
            return

        if channel not in self.channel_subscriptions:
            self.channel_subscriptions[channel] = set()
            if self.redis:
                await self.pubsub.subscribe(f"{self.message_channel_prefix}{channel}")

        self.channel_subscriptions[channel].add(connection_id)

    async def unsubscribe_from_channel(self, connection_id: str, channel: str):
        """
        Unsubscribe a connection from a channel.

        Args:
            connection_id: The connection ID
            channel: The channel to unsubscribe from
        """
        if not self.pubsub:
            return

        if (
            channel in self.channel_subscriptions
            and connection_id in self.channel_subscriptions[channel]
        ):
            self.channel_subscriptions[channel].remove(connection_id)

            if not self.channel_subscriptions[channel]:
                del self.channel_subscriptions[channel]
                if self.redis:
                    await self.pubsub.unsubscribe(f"{self.message_channel_prefix}{channel}")

    async def send_to_connection(self, connection_id: str, message: Any):
        """
        Send a message to a specific connection.

        Args:
            connection_id: The connection ID
            message: The message to send
        """
        if connection_id in self.local_connections:
            websocket = self.local_connections[connection_id]
            await websocket.send_json(message)

    async def broadcast_to_channel(self, channel: str, message: Any):
        """
        Broadcast a message to all connections in a channel.

        Args:
            channel: The channel to broadcast to
            message: The message to send
        """
        # Send to local connections
        await self._broadcast_to_local(channel, message)

        # Publish to Redis for other instances
        if self.redis:
            await self.redis.publish(
                f"{self.message_channel_prefix}{channel}",
                json.dumps({"channel": channel, "message": message}),
            )

    async def _broadcast_to_local(self, channel: str, message: Any):
        if channel in self.channel_subscriptions:
            for connection_id in list(self.channel_subscriptions[channel]):
                if connection_id in self.local_connections:
                    try:
                        await self.local_connections[connection_id].send_json(message)
                    except Exception:  # noqa: BLE001
                        await self.disconnect_connection(connection_id)

    async def handle_client(self, websocket: WebSocket, connection_id: str):
        try:
            while True:
                data = await websocket.receive_json()
                await self.router.handle(websocket, connection_id, data)
        except WebSocketDisconnect:
            await self.disconnect_connection(connection_id)
        except json.JSONDecodeError:
            await websocket.send_json({"error": "Invalid JSON"})
        except Exception as e:  # noqa: BLE001
            print(f"WebSocket error: {e}")  # noqa: T201
            await self.disconnect_connection(connection_id)


@utils.decorators.Singleton
class Router:
    def __init__(self):
        self.handlers: dict[str, Callable] = {}

    def on(self, message_type: str):
        def decorator(handler: Callable):
            self.handlers[message_type] = handler
            return handler

        return decorator

    async def handle(self, websocket: WebSocket, connection_id: str, data: dict[str, Any]):
        if not isinstance(data, dict):
            await websocket.send_json({"error": "Invalid message format"})
            return

        handler = self.handlers.get(data.get("type"))  # type: ignore[valid-type]
        if handler:
            await handler(websocket, connection_id, data)
        else:
            await websocket.send_json({
                "error": "Unknown message type",
                "received_type": data.get("type"),
            })


def get_websocket_manager() -> Manager:
    return Manager()


def get_websocket_router() -> Router:
    return Router()
