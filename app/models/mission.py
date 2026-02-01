import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class MissionStatus(str, enum.Enum):
    """Mission execution status."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MissionPriority(str, enum.Enum):
    """Mission priority level."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class Mission(Base, TimestampMixin):
    """Mission/task to be executed by a robot."""

    __tablename__ = "missions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[MissionStatus] = mapped_column(
        Enum(MissionStatus), nullable=False, default=MissionStatus.PENDING
    )
    priority: Mapped[MissionPriority] = mapped_column(
        Enum(MissionPriority), nullable=False, default=MissionPriority.NORMAL
    )

    # Target location
    target_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_z: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Timing
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Progress tracking
    progress: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100

    # Assignment
    robot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("robots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    robot: Mapped["Robot | None"] = relationship(  # noqa: F821
        "Robot", back_populates="missions"
    )

    def __repr__(self) -> str:
        return f"<Mission {self.name} ({self.status.value})>"
