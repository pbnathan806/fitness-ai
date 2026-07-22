import uuid
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


def _validate_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"'{value}' is not a valid IANA timezone identifier.") from exc
    return value


class ClientCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone_number: str | None = Field(default=None, max_length=20)
    timezone: str = Field(min_length=1, max_length=50)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        return _validate_timezone(value)


class ClientUpdateRequest(BaseModel):
    """Partial update: only the fields provided (non-null) are applied."""

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
    def check_at_least_one_field(self) -> "ClientUpdateRequest":
        if all(
            value is None
            for value in (self.first_name, self.last_name, self.phone_number, self.timezone)
        ):
            raise ValueError("At least one field must be provided to update.")
        return self


class ClientResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: str | None
    timezone: str
    created_at: datetime
    updated_at: datetime


class PaginatedClientsResponse(BaseModel):
    items: list[ClientResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
