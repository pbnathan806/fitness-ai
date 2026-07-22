import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class ClientTrainerAssignment(Base):
    """Join table assigning trainers to clients (many-to-many between clients and trainer_profiles)."""

    __tablename__ = "client_trainer_assignments"
    __table_args__ = (
        UniqueConstraint("client_id", "trainer_id", name="uq_client_trainer"),
        Index("idx_assignment_client", "client_id"),
        Index("idx_assignment_trainer", "trainer_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False
    )
    trainer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trainer_profiles.id"), nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
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
        "Client", foreign_keys=[client_id], back_populates="trainer_assignments"
    )
    trainer: Mapped["TrainerProfile"] = relationship(  # noqa: F821
        "TrainerProfile", foreign_keys=[trainer_id], back_populates="client_assignments"
    )

    def __repr__(self) -> str:
        return (
            f"ClientTrainerAssignment(id={self.id!r}, client_id={self.client_id!r}, "
            f"trainer_id={self.trainer_id!r})"
        )
