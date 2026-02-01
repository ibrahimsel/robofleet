from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession, OperatorUser
from app.models.mission import Mission, MissionStatus
from app.models.robot import Robot
from app.schemas.mission import MissionAssign, MissionCreate, MissionRead, MissionUpdate

router = APIRouter(prefix="/missions", tags=["missions"])


@router.get("", response_model=list[MissionRead])
async def list_missions(
    session: DBSession,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    status_filter: MissionStatus | None = Query(None, alias="status"),
    robot_id: UUID | None = None,
) -> list[Mission]:
    """List all missions with optional filtering."""
    query = select(Mission)

    if status_filter:
        query = query.where(Mission.status == status_filter)
    if robot_id:
        query = query.where(Mission.robot_id == robot_id)

    result = await session.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


@router.post("", response_model=MissionRead, status_code=status.HTTP_201_CREATED)
async def create_mission(
    mission_in: MissionCreate,
    session: DBSession,
    current_user: OperatorUser,
) -> Mission:
    """Create a new mission."""
    mission = Mission(**mission_in.model_dump())
    session.add(mission)
    await session.flush()
    await session.refresh(mission)
    return mission


@router.get("/{mission_id}", response_model=MissionRead)
async def get_mission(
    mission_id: UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> Mission:
    """Get a specific mission by ID."""
    result = await session.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission not found",
        )
    return mission


@router.patch("/{mission_id}", response_model=MissionRead)
async def update_mission(
    mission_id: UUID,
    mission_in: MissionUpdate,
    session: DBSession,
    current_user: OperatorUser,
) -> Mission:
    """Update mission details."""
    result = await session.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission not found",
        )

    update_data = mission_in.model_dump(exclude_unset=True)

    # Handle status transitions
    if "status" in update_data:
        new_status = update_data["status"]
        if new_status == MissionStatus.IN_PROGRESS and not mission.started_at:
            mission.started_at = datetime.now(timezone.utc)
        elif new_status in (MissionStatus.COMPLETED, MissionStatus.FAILED):
            mission.completed_at = datetime.now(timezone.utc)

    for field, value in update_data.items():
        setattr(mission, field, value)

    await session.flush()
    await session.refresh(mission)
    return mission


@router.post("/{mission_id}/assign", response_model=MissionRead)
async def assign_mission(
    mission_id: UUID,
    assign_in: MissionAssign,
    session: DBSession,
    current_user: OperatorUser,
) -> Mission:
    """Assign a robot to a mission."""
    # Get mission
    result = await session.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission not found",
        )

    # Verify mission can be assigned
    if mission.status not in (MissionStatus.PENDING, MissionStatus.ASSIGNED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot assign mission with status {mission.status.value}",
        )

    # Verify robot exists
    result = await session.execute(select(Robot).where(Robot.id == assign_in.robot_id))
    robot = result.scalar_one_or_none()
    if not robot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Robot not found",
        )

    mission.robot_id = assign_in.robot_id
    mission.status = MissionStatus.ASSIGNED

    await session.flush()
    await session.refresh(mission)
    return mission


@router.delete("/{mission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mission(
    mission_id: UUID,
    session: DBSession,
    current_user: OperatorUser,
) -> None:
    """Delete a mission."""
    result = await session.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission not found",
        )
    await session.delete(mission)
