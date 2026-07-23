import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class CheckIn(Base):
    """A daily client wellness snapshot (Task-19).

    Check-ins are immutable: once submitted, a row is never updated or
    deleted, so a client's wellness history always reflects exactly what was
    reported on each day. There is intentionally no repository
    update()/delete() method for this model. Every wellness field is
    optional but at least one must be populated - enforced in the service
    layer via utils.check_in.at_least_one_checkin_field_required, not as a DB
    constraint. Only one check-in may exist per client per calendar day
    (calendar day computed in the client's timezone) - also enforced in the
    service layer via utils.check_in.one_check_in_per_client_per_day.
    """

    __tablename__ = "check_ins"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
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
    # No onupdate=func.now(): check-ins are never updated after creation, so
    # this always equals created_at (kept as a distinct column only to match
    # the audit-timestamp convention shared by every other model).
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    client: Mapped["Client"] = relationship(  # noqa: F821
        "Client", foreign_keys=[client_id], back_populates="check_ins"
    )

    def __repr__(self) -> str:
        return (
            f"CheckIn(id={self.id!r}, client_id={self.client_id!r}, "
            f"submitted_at={self.submitted_at!r})"
        )
