import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SubscriptionPlanCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    duration_days: int = Field(gt=0)
    price: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    max_sessions_per_month: int | None = Field(default=None, gt=0)


class SubscriptionPlanUpdateRequest(BaseModel):
    description: str | None = None
    price: float | None = Field(default=None, gt=0)
    max_sessions_per_month: int | None = Field(default=None, gt=0)
    is_active: bool | None = None


class SubscriptionPlanResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    duration_days: int
    price: float
    currency: str
    max_sessions_per_month: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
