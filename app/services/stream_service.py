import asyncio
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket


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
    Simple in-memory implementation (single instance).
    For multi-instance, use Redis pub/sub.
    """

    def __init__(self):
        self.connections: dict[str, ConnectionState] = {}
        self._lock = asyncio.Lock()

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
        """Broadcast log to all matching subscriptions."""
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


# Global instance (for single-instance deployment)
stream_service = StreamService()
