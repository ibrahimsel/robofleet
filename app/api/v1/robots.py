from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession, OperatorUser
from app.core.websocket import manager
from app.models.robot import Robot
from app.schemas.robot import RobotCreate, RobotRead, RobotStatusUpdate, RobotUpdate

router = APIRouter(prefix="/robots", tags=["robots"])


@router.get("", response_model=list[RobotRead])
async def list_robots(
    session: DBSession,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> list[Robot]:
    """List all robots in the fleet."""
    result = await session.execute(select(Robot).offset(skip).limit(limit))
    return list(result.scalars().all())


@router.post("", response_model=RobotRead, status_code=status.HTTP_201_CREATED)
async def create_robot(
    robot_in: RobotCreate,
    session: DBSession,
    current_user: OperatorUser,
) -> Robot:
    """Register a new robot."""
    # Check serial number uniqueness
    result = await session.execute(
        select(Robot).where(Robot.serial_number == robot_in.serial_number)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Serial number already registered",
        )

    robot = Robot(**robot_in.model_dump())
    session.add(robot)
    await session.flush()
    await session.refresh(robot)
    return robot


@router.get("/{robot_id}", response_model=RobotRead)
async def get_robot(
    robot_id: UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> Robot:
    """Get a specific robot by ID."""
    result = await session.execute(select(Robot).where(Robot.id == robot_id))
    robot = result.scalar_one_or_none()
    if not robot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Robot not found",
        )
    return robot


@router.patch("/{robot_id}", response_model=RobotRead)
async def update_robot(
    robot_id: UUID,
    robot_in: RobotUpdate,
    session: DBSession,
    current_user: OperatorUser,
) -> Robot:
    """Update robot details."""
    result = await session.execute(select(Robot).where(Robot.id == robot_id))
    robot = result.scalar_one_or_none()
    if not robot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Robot not found",
        )

    update_data = robot_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(robot, field, value)

    await session.flush()
    await session.refresh(robot)
    return robot


@router.patch("/{robot_id}/status", response_model=RobotRead)
async def update_robot_status(
    robot_id: UUID,
    status_in: RobotStatusUpdate,
    session: DBSession,
    current_user: OperatorUser,
    background_tasks: BackgroundTasks,
) -> Robot:
    """Update robot status and telemetry."""
    result = await session.execute(select(Robot).where(Robot.id == robot_id))
    robot = result.scalar_one_or_none()
    if not robot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Robot not found",
        )

    update_data = status_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(robot, field, value)

    await session.flush()
    await session.refresh(robot)

    # Broadcast update to WebSocket subscribers
    background_tasks.add_task(
        manager.broadcast_robot_update,
        robot_id,
        {
            "event": "status_update",
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
        },
    )

    return robot


@router.delete("/{robot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_robot(
    robot_id: UUID,
    session: DBSession,
    current_user: OperatorUser,
) -> None:
    """Remove a robot from the fleet."""
    result = await session.execute(select(Robot).where(Robot.id == robot_id))
    robot = result.scalar_one_or_none()
    if not robot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Robot not found",
        )
    await session.delete(robot)
