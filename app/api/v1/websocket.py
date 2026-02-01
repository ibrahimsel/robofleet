from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.websocket import manager
from app.db.session import async_session_maker
from app.models.robot import Robot

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/robots/{robot_id}")
async def robot_status_stream(websocket: WebSocket, robot_id: UUID) -> None:
    """
    WebSocket endpoint for real-time robot status updates.
    
    Connect to receive live updates for a specific robot.
    
    Messages sent to client:
    - {"event": "connected", "robot_id": "...", "robot": {...}}
    - {"event": "status_update", "robot_id": "...", "robot": {...}}
    - {"event": "error", "message": "..."}
    """
    # Verify robot exists before accepting connection
    async with async_session_maker() as session:
        result = await session.execute(select(Robot).where(Robot.id == robot_id))
        robot = result.scalar_one_or_none()

        if not robot:
            await websocket.close(code=4004, reason="Robot not found")
            return

        # Accept and register connection
        await manager.connect(websocket, robot_id)

        # Send initial state
        await websocket.send_json({
            "event": "connected",
            "robot_id": str(robot_id),
            "robot": {
                "id": str(robot.id),
                "name": robot.name,
                "serial_number": robot.serial_number,
                "status": robot.status.value,
                "location_x": robot.location_x,
                "location_y": robot.location_y,
                "location_z": robot.location_z,
                "heading": robot.heading,
                "battery_level": robot.battery_level,
            },
            "subscribers": manager.get_connection_count(robot_id),
        })

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_json()
            
            # Client can send ping to keep alive
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/fleet")
async def fleet_status_stream(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for fleet-wide updates.
    
    Connect to receive updates for ALL robots in the fleet.
    """
    await websocket.accept()
    
    # Get all robots for initial state
    async with async_session_maker() as session:
        result = await session.execute(select(Robot))
        robots = result.scalars().all()
        
        await websocket.send_json({
            "event": "connected",
            "fleet_size": len(robots),
            "robots": [
                {
                    "id": str(r.id),
                    "name": r.name,
                    "status": r.status.value,
                    "battery_level": r.battery_level,
                }
                for r in robots
            ],
        })

    # For fleet-wide, we subscribe to a special "fleet" channel
    # by using UUID(int=0) as a sentinel
    from uuid import UUID as UUIDType
    fleet_id = UUIDType(int=0)
    
    if fleet_id not in manager._connections:
        manager._connections[fleet_id] = set()
    manager._connections[fleet_id].add(websocket)
    manager._subscriptions[websocket] = {fleet_id}

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
