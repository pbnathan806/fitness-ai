import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class PasswordResetToken(Base):
    """A single-use, time-limited password reset token for a user.

    Only the SHA-256 hash of the token is persisted (never the raw value),
    consistent with treating reset tokens as bearer secrets.
    """

    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    # Annotation kept non-Optional (see models/user.py for the reason: SQLAlchemy
    # 2.0.36's Mapped[X | None] resolution crashes on Python 3.14); the column
    # is nullable at the DB/ORM level regardless.
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"PasswordResetToken(id={self.id!r}, user_id={self.user_id!r})"
