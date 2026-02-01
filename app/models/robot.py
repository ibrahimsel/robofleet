import enum
import uuid

from sqlalchemy import Enum, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class RobotStatus(str, enum.Enum):
    """Robot operational status."""

    IDLE = "idle"
    ACTIVE = "active"
    CHARGING = "charging"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    ERROR = "error"


class RobotType(str, enum.Enum):
    """Type of robot in the fleet."""

    AMR = "amr"  # Autonomous Mobile Robot
    AGV = "agv"  # Automated Guided Vehicle
    DRONE = "drone"
    ARM = "arm"  # Robotic Arm
    HUMANOID = "humanoid"


class Robot(Base, TimestampMixin):
    """Robot entity in the fleet."""

    __tablename__ = "robots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    serial_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    robot_type: Mapped[RobotType] = mapped_column(
        Enum(RobotType), nullable=False, default=RobotType.AMR
    )
    status: Mapped[RobotStatus] = mapped_column(
        Enum(RobotStatus), nullable=False, default=RobotStatus.OFFLINE
    )

    # Location
    location_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_z: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading: Mapped[float | None] = mapped_column(Float, nullable=True)  # degrees

    # Metadata
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    battery_level: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-100
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    missions: Mapped[list["Mission"]] = relationship(  # noqa: F821
        "Mission", back_populates="robot", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Robot {self.name} ({self.serial_number})>"
