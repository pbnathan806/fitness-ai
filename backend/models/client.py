import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Client(Base):
    """Client profile for a User acting in the CLIENT role.

    A 1:1 relationship with users: the unique constraint on user_id ensures
    a user has at most one client profile. Clients are created exclusively
    by Super Admins (no self-registration), so created_by/updated_by track
    the acting Super Admin's user id.
    """

    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Annotation kept non-Optional (with nullable=True set explicitly) because
    # SQLAlchemy 2.0.36's Mapped[X | None] resolution crashes on Python 3.14;
    # the column is nullable at the DB/ORM level regardless.
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    # IANA timezone identifier (e.g. "America/New_York", "Asia/Kolkata"); the
    # client's source of truth for schedule and report display per
    # TIMEZONE_REQUIREMENTS.md.
    timezone: Mapped[str] = mapped_column(String(50), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    updated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
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

    user: Mapped["User"] = relationship(  # noqa: F821
        "User", foreign_keys=[user_id], uselist=False
    )
    trainer_assignments: Mapped[list["ClientTrainerAssignment"]] = relationship(  # noqa: F821
        "ClientTrainerAssignment", foreign_keys="ClientTrainerAssignment.client_id", back_populates="client"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(  # noqa: F821
        "Subscription", foreign_keys="Subscription.client_id", back_populates="client"
    )
    sessions: Mapped[list["Session"]] = relationship(  # noqa: F821
        "Session", foreign_keys="Session.client_id", back_populates="client"
    )
    measurements: Mapped[list["Measurement"]] = relationship(  # noqa: F821
        "Measurement", foreign_keys="Measurement.client_id", back_populates="client"
    )

    def __repr__(self) -> str:
        return f"Client(id={self.id!r}, user_id={self.user_id!r})"
