from dataclasses import dataclass, field
from uuid import UUID

from fastapi import WebSocket


@dataclass
class ConnectionManager:
    """Manages WebSocket connections for real-time robot updates."""

    # robot_id -> set of connected websockets
    _connections: dict[UUID, set[WebSocket]] = field(default_factory=dict)
    # websocket -> set of robot_ids it's subscribed to
    _subscriptions: dict[WebSocket, set[UUID]] = field(default_factory=dict)

    async def connect(self, websocket: WebSocket, robot_id: UUID) -> None:
        """Accept connection and subscribe to robot updates."""
        await websocket.accept()

        if robot_id not in self._connections:
            self._connections[robot_id] = set()
        self._connections[robot_id].add(websocket)

        if websocket not in self._subscriptions:
            self._subscriptions[websocket] = set()
        self._subscriptions[websocket].add(robot_id)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove connection and all its subscriptions."""
        if websocket in self._subscriptions:
            for robot_id in self._subscriptions[websocket]:
                if robot_id in self._connections:
                    self._connections[robot_id].discard(websocket)
                    if not self._connections[robot_id]:
                        del self._connections[robot_id]
            del self._subscriptions[websocket]

    async def broadcast_robot_update(self, robot_id: UUID, data: dict) -> None:
        """Send update to all clients subscribed to this robot."""
        if robot_id not in self._connections:
            return

        dead_connections = []
        for websocket in self._connections[robot_id]:
            try:
                await websocket.send_json(data)
            except Exception:
                dead_connections.append(websocket)

        # Clean up dead connections
        for websocket in dead_connections:
            self.disconnect(websocket)

    async def broadcast_fleet_update(self, data: dict) -> None:
        """Send update to ALL connected clients (fleet-wide events)."""
        all_websockets = set()
        for websocket_set in self._connections.values():
            all_websockets.update(websocket_set)

        dead_connections = []
        for websocket in all_websockets:
            try:
                await websocket.send_json(data)
            except Exception:
                dead_connections.append(websocket)

        for websocket in dead_connections:
            self.disconnect(websocket)

    def get_connection_count(self, robot_id: UUID | None = None) -> int:
        """Get number of active connections."""
        if robot_id:
            return len(self._connections.get(robot_id, set()))
        return sum(len(s) for s in self._connections.values())


# Global instance
manager = ConnectionManager()
