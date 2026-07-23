import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


class SubscriptionPaymentStatus(str, enum.Enum):
    PAID = "PAID"
    PENDING = "PENDING"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Subscription(Base):
    """A client's subscription to a plan, tracking its full lifecycle.

    Plan details (name, price, currency, duration) are copied into snapshot
    fields at creation time and are immutable thereafter, so later edits to
    the referenced SubscriptionPlan never alter historical subscriptions.
    Subscriptions are never deleted (Version-1); a client accumulates one row
    per subscription over time. Trainers must never be given plan_price,
    plan_currency, payment_status, or notes (see docs/subscription views).
    """

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False
    )
    subscription_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False
    )

    # Snapshot of the SubscriptionPlan at purchase time; immutable after
    # creation so plan edits never rewrite history.
    plan_name: Mapped[str] = mapped_column(String(100), nullable=False)
    plan_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    plan_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    plan_duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    # Snapshot of SubscriptionPlan.sessions_per_week at purchase time (Task-21);
    # nullable because the source plan field is itself optional.
    plan_sessions_per_week: Mapped[int] = mapped_column(Integer, nullable=True)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status"), nullable=False
    )
    payment_status: Mapped[SubscriptionPaymentStatus] = mapped_column(
        Enum(SubscriptionPaymentStatus, name="subscription_payment_status"),
        nullable=False,
    )

    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Annotation kept non-Optional (with nullable=True set explicitly) because
    # SQLAlchemy 2.0.36's Mapped[X | None] resolution crashes on Python 3.14;
    # the column is nullable at the DB/ORM level regardless.
    notes: Mapped[str] = mapped_column(Text, nullable=True)

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
        "Client", foreign_keys=[client_id], back_populates="subscriptions"
    )
    subscription_plan: Mapped["SubscriptionPlan"] = relationship(  # noqa: F821
        "SubscriptionPlan",
        foreign_keys=[subscription_plan_id],
        back_populates="subscriptions",
    )

    def __repr__(self) -> str:
        return (
            f"Subscription(id={self.id!r}, client_id={self.client_id!r}, "
            f"status={self.status!r})"
        )
