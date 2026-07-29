import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class CheckIn(Base):
    """A session-centric client wellness snapshot (Check-ins V2).

    Check-ins belong to exactly one Session, and a Session may have at most
    one Check-in (enforced via UNIQUE(session_id)). Check-ins represent the
    client's progress since the previous coaching session, and are editable
    by CLIENT/TRAINER/SUPER_ADMIN until check_in_edit_window_days after
    Session.scheduled_start (enforced in the service layer, not as a DB
    constraint). Every wellness field is optional but at least one must be
    populated - enforced in the service layer via
    utils.check_in.at_least_one_checkin_field_required.
    """

    __tablename__ = "check_ins"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False
    )

    # Annotation kept non-Optional (with nullable=True set explicitly) because
    # SQLAlchemy 2.0.36's Mapped[X | None] resolution crashes on Python 3.14;
    # the columns are nullable at the DB/ORM level regardless.
    sleep_hours: Mapped[float] = mapped_column(Numeric(4, 2), nullable=True)
    water_intake_liters: Mapped[float] = mapped_column(Numeric(4, 2), nullable=True)
    energy_level: Mapped[int] = mapped_column(Integer, nullable=True)
    mood: Mapped[int] = mapped_column(Integer, nullable=True)
    workout_completed: Mapped[bool] = mapped_column(Boolean, nullable=True)
    diet_followed: Mapped[bool] = mapped_column(Boolean, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    submitted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

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
        "Client", foreign_keys=[client_id], back_populates="check_ins"
    )
    session: Mapped["Session"] = relationship(  # noqa: F821
        "Session", foreign_keys=[session_id], back_populates="check_in"
    )

    __table_args__ = (UniqueConstraint("session_id", name="uq_check_ins_session_id"),)

    def __repr__(self) -> str:
        return (
            f"CheckIn(id={self.id!r}, session_id={self.session_id!r}, "
            f"client_id={self.client_id!r}, submitted_at={self.submitted_at!r})"
        )
