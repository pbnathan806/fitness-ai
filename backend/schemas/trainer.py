import uuid
from datetime import datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


def _validate_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"'{value}' is not a valid IANA timezone identifier.") from exc
    return value


class TrainerCreateRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone_number: str | None = Field(default=None, max_length=20)
    timezone: str = Field(min_length=1, max_length=50)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        return _validate_timezone(value)


class TrainerUpdateRequest(BaseModel):
    """Full update for SUPER_ADMIN callers via `PUT /trainers/{id}`.

    Only the fields provided (non-null) are applied. `email`, `role`, and
    `is_active` are intentionally absent: `is_active` is only editable via
    `PATCH /trainers/{id}/status`, and email/role are immutable for now.
    """

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone_number: str | None = Field(default=None, max_length=20)
    timezone: str | None = Field(default=None, min_length=1, max_length=50)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validate_timezone(value)

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> "TrainerUpdateRequest":
        if all(
            value is None
            for value in (self.first_name, self.last_name, self.phone_number, self.timezone)
        ):
            raise ValueError("At least one field must be provided to update.")
        return self


class TrainerSelfUpdateRequest(BaseModel):
    """Restricted update for a TRAINER acting on their own profile.

    Trainers may only change `phone_number` and `timezone` (per spec); name,
    email, role, and `is_active` are not editable through this schema.
    """

    phone_number: str | None = Field(default=None, max_length=20)
    timezone: str | None = Field(default=None, min_length=1, max_length=50)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validate_timezone(value)

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> "TrainerSelfUpdateRequest":
        if self.phone_number is None and self.timezone is None:
            raise ValueError("At least one field must be provided to update.")
        return self


class TrainerStatusUpdateRequest(BaseModel):
    is_active: bool


class TrainerResponse(BaseModel):
    id: uuid.UUID
    first_name: str | None
    last_name: str | None
    email: EmailStr
    phone_number: str | None
    timezone: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TrainerCreateResponse(BaseModel):
    id: uuid.UUID
    temporary_password: str


class PaginatedTrainersResponse(BaseModel):
    items: list[TrainerResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class TrainerSummaryResponse(BaseModel):
    assigned_clients: int
    sessions_this_week: int
    completed_sessions_this_month: int
    pending_check_ins: int
    pending_physical_assessments: int


class TrainerPerformanceResponse(BaseModel):
    assigned_clients: int
    completed_sessions: int
    completion_rate: int
    average_check_in_rate: int


class TrainerAvailabilityRequest(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    is_available: bool = True

    @model_validator(mode="after")
    def check_time_range(self) -> "TrainerAvailabilityRequest":
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time.")
        return self


class TrainerAvailabilityResponse(BaseModel):
    id: uuid.UUID
    trainer_id: uuid.UUID
    weekday: int
    start_time: time
    end_time: time
    is_available: bool
    created_at: datetime
