import asyncio
import contextlib
import json
import logging
from typing import Any, TypeVar
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from redis.asyncio import Redis
from redis.asyncio.client import PubSub

from src.core import config, utils
from src.core.websockets.router import Router, get_websocket_router

settings = config.get_settings()
TEvent = TypeVar("TEvent", bound=BaseModel)


@utils.decorators.Singleton
class Manager:
    def __init__(self):
        self.redis_url = settings.REDIS.URL
        self.redis: Redis | None = None
        self.local_connections: dict[UUID, WebSocket] = {}
        self.channel_subscriptions: dict[str, set[UUID]] = {}

        # Pub/sub channels
        self.connection_channel: str = "websocket:connections"
        self.message_channel_prefix: str = "websocket:messages:"

        self.pubsub: PubSub | None = None
        self._listener_task = None

        self.router: Router = get_websocket_router()

        self.logger = logging.getLogger(f"websocket.{self.__class__.__name__.lower()}")

    async def connect_to_redis(self):
        """Initialize Redis connection and pub/sub"""
        self.logger.info("Connecting to Redis...")
        try:
            self.redis = Redis.from_url(self.redis_url)
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe(self.connection_channel)
            self._listener_task = asyncio.create_task(self._listen_to_redis())
            self.logger.info("Successfully connected to Redis and started listener")
        except Exception:
            self.logger.exception("Failed to connect to Redis:")
            raise

    async def disconnect_from_redis(self):
        """Cleanup Redis connection"""
        self.logger.info("Disconnecting from Redis...")
        try:
            if self._listener_task:
                self._listener_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._listener_task
                self.logger.debug("Listener task cancelled")

            if self.redis:
                await self.redis.aclose()
                self.logger.info("Redis connection closed")
        except Exception:
            self.logger.exception("Error during disconnection:")
        finally:
            self.redis = None
            self.pubsub = None
            self._listener_task = None

    async def _listen_to_redis(self):
        """Listen for messages from Redis pub/sub"""
        self.logger.debug("Starting Redis listener")
        if not self.pubsub:
            self.logger.warning("PubSub not initialized, cannot listen to Redis")
            return

        try:
            async for message in self.pubsub.listen():
                if message["type"] != "message":
                    continue

                data = json.loads(message["data"])

                # Decode the channel from bytes to string
                channel = (
                    message["channel"].decode("utf-8")
                    if isinstance(message["channel"], bytes)
                    else message["channel"]
                )

                self.logger.debug("Received message on channel %s: %s", channel, data)

                # Handle connection events
                if channel == self.connection_channel:
                    if data["type"] == "disconnect":
                        connection_id = data["connection_id"]
                        if connection_id in self.local_connections:
                            await self._local_disconnect(connection_id)

                # Handle message events
                elif channel.startswith(self.message_channel_prefix):
                    channel_name = channel[len(self.message_channel_prefix) :]
                    await self._broadcast_to_local(channel_name, data["message"])
        except Exception:
            self.logger.exception("Error in Redis listener:")
            raise

    async def accept_connection(self, websocket: WebSocket, connection_id: UUID) -> UUID:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            connection_id: Optional custom connection ID

        Returns:
            The connection ID
        """
        self.logger.info("Accepting new connection with ID: %s", connection_id)
        self.local_connections[connection_id] = websocket

        # Notify other instances about new connection
        if self.redis:
            try:
                await self.redis.publish(
                    self.connection_channel,
                    json.dumps({"type": "connect", "connection_id": str(connection_id)}),
                )
                self.logger.debug("Published connection event for %s", connection_id)
            except Exception:
                self.logger.exception("Failed to publish connection event:")

        return connection_id

    async def disconnect_connection(self, connection_id: UUID):
        """
        Disconnect a WebSocket connection.

        Args:
            connection_id: The connection ID to disconnect
        """
        self.logger.info("Disconnecting connection: %s", connection_id)
        if connection_id in self.local_connections:
            await self._local_disconnect(connection_id)

        # Notify other instances about disconnection
        if self.redis:
            try:
                await self.redis.publish(
                    self.connection_channel,
                    json.dumps({"type": "disconnect", "connection_id": str(connection_id)}),
                )
                self.logger.debug("Published disconnection event for %s", connection_id)
            except Exception:
                self.logger.exception("Failed to publish disconnection event:")

    async def _local_disconnect(self, connection_id: UUID):
        """Handle local disconnection cleanup"""
        self.logger.debug("Processing local disconnect for %s", connection_id)
        if connection_id in self.local_connections:
            websocket = self.local_connections[connection_id]
            try:
                await websocket.close()
                self.logger.debug("Closed WebSocket for %s", connection_id)
            except Exception as e:  # noqa: BLE001
                self.logger.warning("Error closing WebSocket for %s: %s", connection_id, e)

            del self.local_connections[connection_id]

            # Remove from all channel subscriptions
            for channel in list(self.channel_subscriptions.keys()):
                if connection_id in self.channel_subscriptions[channel]:
                    self.channel_subscriptions[channel].remove(connection_id)
                    if not self.channel_subscriptions[channel]:
                        del self.channel_subscriptions[channel]
                        self.logger.debug("Removed empty channel: %s", channel)

    async def subscribe_to_channel(self, connection_id: UUID, channel: str):
        """
        Subscribe a connection to a channel.

        Args:
            connection_id: The connection ID
            channel: The channel to subscribe to
        """
        self.logger.info("Subscribing %s to channel %s", connection_id, channel)
        if connection_id not in self.local_connections:
            self.logger.warning("Connection %s not found", connection_id)
            return

        if not self.pubsub:
            self.logger.warning("PubSub not initialized, cannot subscribe")
            return

        if channel not in self.channel_subscriptions:
            self.channel_subscriptions[channel] = set()
            if self.redis:
                try:
                    await self.pubsub.subscribe(f"{self.message_channel_prefix}{channel}")
                    self.logger.debug("Subscribed to Redis channel: %s", channel)
                except Exception:
                    self.logger.exception("Failed to subscribe to Redis channel")
                    return

        self.channel_subscriptions[channel].add(connection_id)
        self.logger.debug("Added %s to channel %s subscriptions", connection_id, channel)

    async def unsubscribe_from_channel(self, connection_id: UUID, channel: str):
        """
        Unsubscribe a connection from a channel.

        Args:
            connection_id: The connection ID
            channel: The channel to unsubscribe from
        """
        self.logger.info("Unsubscribing %s from channel %s", connection_id, channel)
        if not self.pubsub:
            self.logger.warning("PubSub not initialized, cannot unsubscribe")
            return

        if (
            channel in self.channel_subscriptions
            and connection_id in self.channel_subscriptions[channel]
        ):
            self.channel_subscriptions[channel].remove(connection_id)

            if not self.channel_subscriptions[channel]:
                del self.channel_subscriptions[channel]
                if self.redis:
                    try:
                        await self.pubsub.unsubscribe(f"{self.message_channel_prefix}{channel}")
                        self.logger.debug("Unsubscribed from Redis channel: %s", channel)
                    except Exception:
                        self.logger.exception("Failed to unsubscribe from Redis channel:")

    async def send_to_connection(self, connection_id: UUID, message: Any):
        """
        Send a message to a specific connection.

        Args:
            connection_id: The connection ID
            message: The message to send
        """
        self.logger.debug("Sending message to connection %s", connection_id)
        if connection_id in self.local_connections:
            websocket = self.local_connections[connection_id]
            try:
                await websocket.send_json(json.loads(message))
            except Exception:
                self.logger.exception("Failed to send message to %s:", connection_id)
                await self.disconnect_connection(connection_id)

    async def broadcast_to_channel(self, channel: str, message: Any):
        """
        Broadcast a message to all connections in a channel.

        Args:
            channel: The channel to broadcast to
            message: The message to send
        """
        self.logger.info("Broadcasting message to channel %s", channel)
        # Publish to Redis for other instances
        if self.redis:
            try:
                await self.redis.publish(
                    f"{self.message_channel_prefix}{channel}",
                    json.dumps({"channel": str(channel), "message": message}),
                )
                self.logger.debug("Published message to Redis channel %s", channel)
            except Exception:
                self.logger.exception("Failed to publish to Redis channel %s:", channel)
        else:
            await self._broadcast_to_local(channel, message)

    async def _broadcast_to_local(self, channel: str, message: Any):
        self.logger.debug("Broadcasting locally to channel %s", channel)
        if channel in self.channel_subscriptions:
            for connection_id in list(self.channel_subscriptions[channel]):
                if connection_id in self.local_connections:
                    try:
                        await self.local_connections[connection_id].send_json(json.loads(message))
                        self.logger.debug("Sent message to %s", connection_id)
                    except Exception as e:  # noqa: BLE001
                        self.logger.warning("Failed to send to %s: %s", connection_id, e)
                        await self.disconnect_connection(connection_id)

    async def send_event_to_connection(self, connection_id: UUID, event: BaseModel):
        """
        Send a Pydantic event to a specific connection.

        Args:
            connection_id: The connection ID to send to
            event: Pydantic model representing the event
        """
        self.logger.info("Sending event to connection %s", connection_id)
        await self.send_to_connection(connection_id, event.model_dump_json())

    async def broadcast_event_to_channel(self, channel: str, event: BaseModel):
        """
        Broadcast a Pydantic event to all connections in a channel.

        Args:
            channel: The channel to broadcast to
            event: Pydantic model representing the event
        """
        self.logger.info("Broadcasting event to channel %s", channel)
        await self.broadcast_to_channel(channel, event.model_dump_json())

    async def handle_client(
        self, websocket: WebSocket, connection_id: UUID, session_id: UUID, user: BaseModel
    ):
        self.logger.info("Handling client connection %s", connection_id)
        try:
            while True:
                data = await websocket.receive_json()
                self.logger.debug("Received message from %s: %s", connection_id, data)
                await self.router.handle(websocket, connection_id, session_id, data, user)
        except WebSocketDisconnect:
            self.logger.info("Client %s disconnected", connection_id)
            await self.disconnect_connection(connection_id)
        except json.JSONDecodeError:
            self.logger.warning("Invalid JSON received from %s", connection_id)
            await websocket.send_json({"error": "Invalid JSON"})
        except Exception:
            self.logger.exception("Error in handle_client for %s", connection_id)
            await self.disconnect_connection(connection_id)


def get_websocket_manager() -> Manager:
    return Manager()
