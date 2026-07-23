import uuid
from datetime import date, datetime

from pydantic import BaseModel

from models.subscription import SubscriptionPaymentStatus, SubscriptionStatus


class SubscriptionCreateRequest(BaseModel):
    client_id: uuid.UUID
    subscription_plan_id: uuid.UUID
    start_date: date | None = None
    auto_renew: bool = False
    notes: str | None = None


class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    subscription_plan_id: uuid.UUID
    plan_name: str
    plan_price: float
    plan_currency: str
    plan_duration_days: int
    plan_sessions_per_week: int | None
    start_date: date
    end_date: date
    status: SubscriptionStatus
    payment_status: SubscriptionPaymentStatus
    auto_renew: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class PaginatedSubscriptionsResponse(BaseModel):
    items: list[SubscriptionResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class ClientSubscriptionResponse(BaseModel):
    id: uuid.UUID
    plan_name: str
    plan_price: float
    plan_currency: str
    payment_status: SubscriptionPaymentStatus
    status: SubscriptionStatus
    start_date: date
    end_date: date


class SubscriptionEligibilityResponse(BaseModel):
    client_id: uuid.UUID
    plan_name: str
    status: SubscriptionStatus
    end_date: date
    can_schedule_sessions: bool


class SubscriptionUpdateRequest(BaseModel):
    """Immutable fields (client_id, subscription_plan_id, plan_name, plan_price,
    plan_currency, plan_duration_days, start_date) are accepted here only so
    the service layer can detect and reject attempts to change them; they are
    never applied to the underlying subscription.
    """

    status: SubscriptionStatus | None = None
    payment_status: SubscriptionPaymentStatus | None = None
    end_date: date | None = None
    auto_renew: bool | None = None
    notes: str | None = None
    client_id: uuid.UUID | None = None
    subscription_plan_id: uuid.UUID | None = None
    plan_name: str | None = None
    plan_price: float | None = None
    plan_currency: str | None = None
    plan_duration_days: int | None = None
    start_date: date | None = None
