import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class SessionStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"


class SessionMeetingType(str, enum.Enum):
    GOOGLE_MEET = "GOOGLE_MEET"
    ZOOM = "ZOOM"
    WHATSAPP = "WHATSAPP"
    PHONE = "PHONE"
    IN_PERSON = "IN_PERSON"


class SessionAttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    BOTH_PRESENT = "BOTH_PRESENT"
    CLIENT_NO_SHOW = "CLIENT_NO_SHOW"
    TRAINER_NO_SHOW = "TRAINER_NO_SHOW"
    LATE = "LATE"
    RESCHEDULED = "RESCHEDULED"


class Session(Base):
    """A scheduled coaching interaction between a Client and a TrainerProfile.

    Version-1 scheduling philosophy: sessions are never auto-generated from
    subscriptions. A Client subscribes, a Trainer is assigned, the Trainer
    agrees on a schedule with the client out of band, and the Trainer (or a
    SUPER_ADMIN acting as an override/escalation role) manually creates each
    Session row. Bulk creation (e.g. recurring weekly slots) is a Task-17.2
    concern and is intentionally not implemented here.

    Business rules enforced in later tasks (not this one):
      1. Client must have an eligible subscription.
      2. Trainer must be assigned to the client.
      3. Sessions cannot be scheduled in the past.
      4. Trainers can only manage their assigned clients.
      5. Clients can only view their own sessions.
      6. SUPER_ADMIN has full access.
      7. Session overlap validation will be implemented later.
      8. Remaining subscription session validation will be implemented later.
    """

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False
    )
    trainer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trainer_profiles.id"), nullable=False
    )

    scheduled_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    scheduled_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60
    )

    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status"), nullable=False
    )

    meeting_type: Mapped[SessionMeetingType] = mapped_column(
        Enum(SessionMeetingType, name="session_meeting_type"), nullable=False
    )
    # Annotation kept non-Optional (with nullable=True set explicitly) because
    # SQLAlchemy 2.0.36's Mapped[X | None] resolution crashes on Python 3.14;
    # the column is nullable at the DB/ORM level regardless.
    meeting_link: Mapped[str] = mapped_column(String(500), nullable=True)

    trainer_notes: Mapped[str] = mapped_column(Text, nullable=True)
    trainer_feedback: Mapped[str] = mapped_column(Text, nullable=True)
    homework: Mapped[str] = mapped_column(Text, nullable=True)
    next_session_focus: Mapped[str] = mapped_column(Text, nullable=True)

    # Nullable: attendance is only known once the session has taken place,
    # so a freshly SCHEDULED session has no attendance_status yet.
    attendance_status: Mapped[SessionAttendanceStatus] = mapped_column(
        Enum(SessionAttendanceStatus, name="session_attendance_status"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    client: Mapped["Client"] = relationship(  # noqa: F821
        "Client", foreign_keys=[client_id], back_populates="sessions"
    )
    trainer: Mapped["TrainerProfile"] = relationship(  # noqa: F821
        "TrainerProfile", foreign_keys=[trainer_id], back_populates="sessions"
    )

    def __repr__(self) -> str:
        return (
            f"Session(id={self.id!r}, client_id={self.client_id!r}, "
            f"trainer_id={self.trainer_id!r}, status={self.status!r})"
        )
