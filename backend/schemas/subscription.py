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
    status: SubscriptionStatus | None = None
    payment_status: SubscriptionPaymentStatus | None = None
    end_date: date | None = None
    auto_renew: bool | None = None
    notes: str | None = None
