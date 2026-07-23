import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, field_validator

from models.session import SessionAttendanceStatus, SessionMeetingType, SessionStatus
from utils.session import Weekday


class SessionCreateRequest(BaseModel):
    client_id: uuid.UUID
    # Required for SUPER_ADMIN (who is not themselves a trainer); optional for
    # TRAINER, whose own trainer profile is inferred from the access token.
    trainer_id: uuid.UUID | None = None
    scheduled_start: datetime
    duration_minutes: int = 60
    meeting_type: SessionMeetingType
    meeting_link: str | None = None
    trainer_notes: str | None = None

    @field_validator("scheduled_start")
    @classmethod
    def _require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("scheduled_start must be timezone-aware.")
        return value


class SessionBulkCreateRequest(BaseModel):
    client_id: uuid.UUID
    trainer_id: uuid.UUID | None = None
    start_date: date
    end_date: date
    days: list[Weekday]
    start_time: time
    duration_minutes: int = 60
    meeting_type: SessionMeetingType


class SessionResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    trainer_id: uuid.UUID
    scheduled_start: datetime
    scheduled_end: datetime
    duration_minutes: int
    status: SessionStatus
    meeting_type: SessionMeetingType
    meeting_link: str | None
    trainer_notes: str | None
    trainer_feedback: str | None
    homework: str | None
    next_session_focus: str | None
    attendance_status: SessionAttendanceStatus | None
    created_at: datetime
    updated_at: datetime


class PaginatedSessionsResponse(BaseModel):
    items: list[SessionResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class SessionBulkCreateResponse(BaseModel):
    sessions_created: int
    sessions_skipped: int
    skipped_reasons: list[str]


class SessionUpdateRequest(BaseModel):
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    status: SessionStatus | None = None
    meeting_type: SessionMeetingType | None = None
    meeting_link: str | None = None
    trainer_notes: str | None = None
    attendance_status: SessionAttendanceStatus | None = None


class SessionNotesUpdateRequest(BaseModel):
    trainer_notes: str | None = None
    trainer_feedback: str | None = None
    homework: str | None = None
    next_session_focus: str | None = None


class SessionAttendanceUpdateRequest(BaseModel):
    attendance_status: SessionAttendanceStatus
