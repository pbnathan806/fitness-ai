import uuid
from datetime import date, datetime

from pydantic import BaseModel, field_validator


class MeasurementCreateRequest(BaseModel):
    client_id: uuid.UUID
    # Defaults to "now" (service layer) when omitted; must be timezone-aware
    # when provided so it can be safely converted to the client's local date.
    recorded_at: datetime | None = None
    weight_kg: float | None = None
    body_fat_percentage: float | None = None
    chest_cm: float | None = None
    waist_cm: float | None = None
    hips_cm: float | None = None
    left_arm_cm: float | None = None
    right_arm_cm: float | None = None
    left_thigh_cm: float | None = None
    right_thigh_cm: float | None = None
    resting_heart_rate: int | None = None

    @field_validator("recorded_at")
    @classmethod
    def _require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("recorded_at must be timezone-aware.")
        return value


class MeasurementResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    weight_kg: float | None
    body_fat_percentage: float | None
    chest_cm: float | None
    waist_cm: float | None
    hips_cm: float | None
    left_arm_cm: float | None
    right_arm_cm: float | None
    left_thigh_cm: float | None
    right_thigh_cm: float | None
    resting_heart_rate: int | None
    recorded_by: uuid.UUID
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime


class PaginatedMeasurementsResponse(BaseModel):
    items: list[MeasurementResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class LatestMeasurementResponse(BaseModel):
    weight_kg: float | None
    previous_weight_kg: float | None
    weight_change: float | None
    body_fat_percentage: float | None
    previous_body_fat_percentage: float | None
    body_fat_change: float | None
    chest_cm: float | None
    previous_chest_cm: float | None
    chest_change: float | None
    waist_cm: float | None
    previous_waist_cm: float | None
    waist_change: float | None
    hips_cm: float | None
    previous_hips_cm: float | None
    hips_change: float | None
    left_arm_cm: float | None
    previous_left_arm_cm: float | None
    left_arm_change: float | None
    right_arm_cm: float | None
    previous_right_arm_cm: float | None
    right_arm_change: float | None
    left_thigh_cm: float | None
    previous_left_thigh_cm: float | None
    left_thigh_change: float | None
    right_thigh_cm: float | None
    previous_right_thigh_cm: float | None
    right_thigh_change: float | None
    resting_heart_rate: int | None
    previous_resting_heart_rate: int | None
    resting_heart_rate_change: int | None
    recorded_at: date | None
