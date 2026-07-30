import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Measurement(Base):
    """A single point-in-time client body-measurement snapshot (Task-18).

    Measurements are never deleted, so a client's measurement history is
    always preserved. A SUPER_ADMIN, or a TRAINER assigned to the client, may
    edit one until measurement_edit_window_days after recorded_at (enforced
    in the service layer, not as a DB constraint); CLIENT is always
    read-only. Every body-measurement field is optional (fitness assessments
    are often partial) but at least one must be populated - enforced in the
    service layer via utils.measurement.at_least_one_measurement_required,
    not as a DB constraint.
    """

    __tablename__ = "measurements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False
    )

    # Annotation kept non-Optional (with nullable=True set explicitly) because
    # SQLAlchemy 2.0.36's Mapped[X | None] resolution crashes on Python 3.14;
    # the columns are nullable at the DB/ORM level regardless.
    weight_kg: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    body_fat_percentage: Mapped[float] = mapped_column(Numeric(4, 1), nullable=True)
    chest_cm: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    waist_cm: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    hips_cm: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    left_arm_cm: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    right_arm_cm: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    left_thigh_cm: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    right_thigh_cm: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    resting_heart_rate: Mapped[int] = mapped_column(Integer, nullable=True)

    recorded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

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
        "Client", foreign_keys=[client_id], back_populates="measurements"
    )

    def __repr__(self) -> str:
        return (
            f"Measurement(id={self.id!r}, client_id={self.client_id!r}, "
            f"recorded_at={self.recorded_at!r})"
        )
