import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class PhysicalAssessment(Base):
    """A single point-in-time client physical assessment snapshot (Task-18,
    renamed from Measurement).

    Physical assessments are never deleted, so a client's physical assessment
    history is always preserved. A SUPER_ADMIN, or a TRAINER assigned to the
    client, may edit one until physical_assessment_edit_window_days after
    recorded_at (enforced in the service layer, not as a DB constraint);
    CLIENT is always read-only. Every body-measurement field is optional
    (fitness assessments are often partial) but at least one must be
    populated - enforced in the service layer via
    utils.physical_assessment.at_least_one_physical_assessment_required, not
    as a DB constraint.

    front_photo_url/back_photo_url/side_photo_url are groundwork for a
    not-yet-built photo upload capability: nullable, always None today, not
    exposed on any create/update request schema (no upload mechanism exists
    yet to populate them). Deliberately not restricted to a storage provider -
    just an external path/URL string, populated by whatever storage backend
    is chosen later.
    """

    __tablename__ = "physical_assessments"

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

    # Groundwork only - see class docstring. No write path exists yet.
    front_photo_url: Mapped[str] = mapped_column(String(2048), nullable=True)
    back_photo_url: Mapped[str] = mapped_column(String(2048), nullable=True)
    side_photo_url: Mapped[str] = mapped_column(String(2048), nullable=True)

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
        "Client", foreign_keys=[client_id], back_populates="physical_assessments"
    )

    def __repr__(self) -> str:
        return (
            f"PhysicalAssessment(id={self.id!r}, client_id={self.client_id!r}, "
            f"recorded_at={self.recorded_at!r})"
        )
