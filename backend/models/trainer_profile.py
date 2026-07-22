import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class TrainerProfile(Base):
    """Trainer profile for a User acting in the TRAINER role.

    A 1:1 relationship with users: the unique constraint on user_id ensures
    a user has at most one trainer profile.
    """

    __tablename__ = "trainer_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    # Annotation kept non-Optional (with nullable=True set explicitly) because
    # SQLAlchemy 2.0.36's Mapped[X | None] resolution crashes on Python 3.14;
    # the column is nullable at the DB/ORM level regardless.
    specialization: Mapped[str] = mapped_column(String(255), nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=True)
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    # IANA timezone identifier (e.g. "America/New_York", "Asia/Kolkata"), consistent
    # with models/client.py, per TIMEZONE_REQUIREMENTS.md.
    timezone: Mapped[str] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=True)
    is_accepting_clients: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
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
        "User", foreign_keys=[user_id], uselist=False, back_populates="trainer_profile"
    )

    def __repr__(self) -> str:
        return f"TrainerProfile(id={self.id!r}, user_id={self.user_id!r})"
