import uuid
from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Time, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class TrainerAvailability(Base):
    """A recurring weekly availability slot for a trainer.

    `weekday` follows Python's `date.weekday()` convention (0=Monday..6=Sunday),
    consistent with the week-boundary helpers in `utils/dashboard.py`.
    """

    __tablename__ = "trainer_availability"
    __table_args__ = (Index("idx_availability_trainer", "trainer_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trainer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trainer_profiles.id"), nullable=False
    )
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    trainer: Mapped["TrainerProfile"] = relationship(  # noqa: F821
        "TrainerProfile", foreign_keys=[trainer_id], back_populates="availability_slots"
    )

    def __repr__(self) -> str:
        return (
            f"TrainerAvailability(id={self.id!r}, trainer_id={self.trainer_id!r}, "
            f"weekday={self.weekday!r})"
        )
