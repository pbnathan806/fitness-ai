import uuid
from datetime import datetime

from pydantic import BaseModel


class AssignmentCreateRequest(BaseModel):
    client_id: uuid.UUID
    trainer_id: uuid.UUID
    is_primary: bool = False


class AssignmentResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    trainer_id: uuid.UUID
    is_primary: bool
    assigned_at: datetime
    created_at: datetime
    updated_at: datetime


class PaginatedAssignmentsResponse(BaseModel):
    items: list[AssignmentResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class AssignedClientResponse(BaseModel):
    assignment_id: uuid.UUID
    client_id: uuid.UUID
    first_name: str
    last_name: str
    timezone: str
    is_primary: bool


class AssignedTrainerResponse(BaseModel):
    assignment_id: uuid.UUID
    trainer_id: uuid.UUID
    first_name: str | None
    last_name: str | None
    specialization: str | None
    experience_years: int | None
    bio: str | None
    timezone: str | None
    country: str | None
    is_primary: bool
