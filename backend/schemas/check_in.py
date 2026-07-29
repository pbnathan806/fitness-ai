import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class CheckInCreateRequest(BaseModel):
    session_id: uuid.UUID
    sleep_hours: float | None = None
    water_intake_liters: float | None = None
    energy_level: int | None = None
    mood: int | None = None
    workout_completed: bool | None = None
    diet_followed: bool | None = None
    notes: str | None = None

    @field_validator("sleep_hours")
    @classmethod
    def _validate_sleep_hours(cls, value: float | None) -> float | None:
        if value is not None and not (0 <= value <= 24):
            raise ValueError("sleep_hours must be between 0 and 24.")
        return value

    @field_validator("water_intake_liters")
    @classmethod
    def _validate_water_intake_liters(cls, value: float | None) -> float | None:
        if value is not None and not (0 <= value <= 20):
            raise ValueError("water_intake_liters must be between 0 and 20.")
        return value

    @field_validator("energy_level")
    @classmethod
    def _validate_energy_level(cls, value: int | None) -> int | None:
        if value is not None and not (1 <= value <= 5):
            raise ValueError("energy_level must be between 1 and 5.")
        return value

    @field_validator("mood")
    @classmethod
    def _validate_mood(cls, value: int | None) -> int | None:
        if value is not None and not (1 <= value <= 5):
            raise ValueError("mood must be between 1 and 5.")
        return value


class CheckInUpdateRequest(BaseModel):
    sleep_hours: float | None = None
    water_intake_liters: float | None = None
    energy_level: int | None = None
    mood: int | None = None
    workout_completed: bool | None = None
    diet_followed: bool | None = None
    notes: str | None = None

    @field_validator("sleep_hours")
    @classmethod
    def _validate_sleep_hours(cls, value: float | None) -> float | None:
        if value is not None and not (0 <= value <= 24):
            raise ValueError("sleep_hours must be between 0 and 24.")
        return value

    @field_validator("water_intake_liters")
    @classmethod
    def _validate_water_intake_liters(cls, value: float | None) -> float | None:
        if value is not None and not (0 <= value <= 20):
            raise ValueError("water_intake_liters must be between 0 and 20.")
        return value

    @field_validator("energy_level")
    @classmethod
    def _validate_energy_level(cls, value: int | None) -> int | None:
        if value is not None and not (1 <= value <= 5):
            raise ValueError("energy_level must be between 1 and 5.")
        return value

    @field_validator("mood")
    @classmethod
    def _validate_mood(cls, value: int | None) -> int | None:
        if value is not None and not (1 <= value <= 5):
            raise ValueError("mood must be between 1 and 5.")
        return value


class CheckInResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    client_id: uuid.UUID
    sleep_hours: float | None
    water_intake_liters: float | None
    energy_level: int | None
    mood: int | None
    workout_completed: bool | None
    diet_followed: bool | None
    notes: str | None
    submitted_by: uuid.UUID
    submitted_at: datetime
    created_at: datetime
    updated_at: datetime


class PaginatedCheckInsResponse(BaseModel):
    items: list[CheckInResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class PendingCheckInResponse(BaseModel):
    session_id: uuid.UUID
    client_id: uuid.UUID
    client_name: str
    scheduled_start: datetime
    days_pending: int
