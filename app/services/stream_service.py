import asyncio
import json
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket
import redis.asyncio as redis

from app.config import get_settings


@dataclass
class Subscription:
    """Represents a client subscription to log events."""
    subscription_id: str
    filters: dict[str, Any] = field(default_factory=dict)
    paused: bool = False


@dataclass
class ConnectionState:
    """Tracks state for a WebSocket connection."""
    websocket: WebSocket
    session_id: str
    subscriptions: dict[str, Subscription] = field(default_factory=dict)


class StreamService:
    """
    Manages WebSocket connections and message distribution.
    Uses Redis pub/sub for multi-instance support.
    """
    
    CHANNEL = "strym:logs"

    def __init__(self):
        self.connections: dict[str, ConnectionState] = {}
        self._lock = asyncio.Lock()
        self._redis: redis.Redis | None = None
        self._pubsub: redis.client.PubSub | None = None
        self._listener_task: asyncio.Task | None = None

    async def init(self) -> None:
        """Initialize Redis connection and start listener."""
        settings = get_settings()
        self._redis = redis.from_url(settings.redis_url)
        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(self.CHANNEL)
        self._listener_task = asyncio.create_task(self._listen_for_messages())
        print(f"Redis pub/sub initialized on channel: {self.CHANNEL}")

    async def close(self) -> None:
        """Close Redis connection."""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        if self._pubsub:
            await self._pubsub.unsubscribe(self.CHANNEL)
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()
        print("Redis pub/sub closed")

    async def _listen_for_messages(self) -> None:
        """Listen for messages from Redis and broadcast to local connections."""
        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    await self._broadcast_to_local(data)
        except asyncio.CancelledError:
            pass

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        """Register new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.connections[session_id] = ConnectionState(
                websocket=websocket,
                session_id=session_id,
            )

    async def disconnect(self, session_id: str) -> None:
        """Remove WebSocket connection."""
        async with self._lock:
            if session_id in self.connections:
                del self.connections[session_id]

    async def subscribe(
        self,
        session_id: str,
        subscription_id: str,
        filters: dict[str, Any],
    ) -> None:
        """Subscribe connection to log events with filters."""
        async with self._lock:
            if session_id in self.connections:
                self.connections[session_id].subscriptions[subscription_id] = Subscription(
                    subscription_id=subscription_id,
                    filters=filters,
                )

    async def unsubscribe(self, session_id: str, subscription_id: str) -> None:
        """Remove subscription."""
        async with self._lock:
            if session_id in self.connections:
                self.connections[session_id].subscriptions.pop(subscription_id, None)

    async def broadcast_log(self, log_data: dict) -> None:
        """Publish log to Redis channel (all instances will receive it)."""
        if self._redis:
            await self._redis.publish(self.CHANNEL, json.dumps(log_data))
        else:
            # Fallback to local broadcast if Redis not available
            await self._broadcast_to_local(log_data)

    async def _broadcast_to_local(self, log_data: dict) -> None:
        """Broadcast log to local WebSocket connections."""
        async with self._lock:
            connections = list(self.connections.values())

        for conn in connections:
            for sub in conn.subscriptions.values():
                if sub.paused:
                    continue
                
                if self._matches_filters(log_data, sub.filters):
                    try:
                        await conn.websocket.send_json({
                            "type": "log",
                            "subscription_id": sub.subscription_id,
                            "data": log_data,
                        })
                    except Exception:
                        # Connection might be closed
                        await self.disconnect(conn.session_id)
                        break

    def _matches_filters(self, log_data: dict, filters: dict) -> bool:
        """Check if log matches subscription filters."""
        if not filters:
            return True

        # Filter by source_app
        if "source_app" in filters:
            apps = filters["source_app"]
            if isinstance(apps, list):
                if log_data.get("source", {}).get("app_id") not in apps:
                    return False
            elif log_data.get("source", {}).get("app_id") != apps:
                return False

        # Filter by severity
        if "severity" in filters:
            severities = filters["severity"]
            if isinstance(severities, list):
                if log_data.get("severity") not in severities:
                    return False
            elif log_data.get("severity") != severities:
                return False

        # Filter by min_severity
        if "min_severity" in filters:
            severity_order = {"debug": 0, "info": 1, "warn": 2, "error": 3, "fatal": 4}
            min_level = severity_order.get(filters["min_severity"], 0)
            log_level = severity_order.get(log_data.get("severity", "debug"), 0)
            if log_level < min_level:
                return False

        return True


# Global instance
stream_service = StreamService()
