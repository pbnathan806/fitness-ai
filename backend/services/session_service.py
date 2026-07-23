import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from core.constants import RoleName
from models.session import Session, SessionAttendanceStatus, SessionMeetingType, SessionStatus
from repositories.assignment_repository import AssignmentRepository
from repositories.client_repository import ClientRepository
from repositories.session_repository import SessionRepository
from repositories.subscription_plan_repository import SubscriptionPlanRepository
from repositories.subscription_repository import SubscriptionRepository
from utils.session import generate_bulk_session_starts
from utils.subscription import can_schedule_sessions


class ForbiddenError(Exception):
    """Raised when the acting user's role does not permit the requested action."""


class ClientNotFoundError(Exception):
    """Raised when no client profile exists for the requested identifier."""


class TrainerNotFoundError(Exception):
    """Raised when no trainer profile exists for the requested identifier."""


class TrainerNotAssignedError(Exception):
    """Raised when the resolved trainer is not assigned to the requested client."""


class SubscriptionNotEligibleError(Exception):
    """Raised when the client has no subscription eligible for scheduling sessions."""


class SessionInPastError(Exception):
    """Raised when a session is scheduled to start at or before the current time."""


class ClientOverlapError(Exception):
    """Raised when the client already has a non-cancelled session overlapping the slot."""


class TrainerOverlapError(Exception):
    """Raised when the trainer already has a non-cancelled session overlapping the slot."""


class SessionLimitReachedError(Exception):
    """Raised when the client has no remaining sessions on their subscription plan."""


class SessionNotFoundError(Exception):
    """Raised when no session exists for the requested identifier."""


class AttendanceImmutableError(Exception):
    """Raised when attendance is edited after the session's status is COMPLETED."""


@dataclass(frozen=True)
class SessionDetail:
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


@dataclass(frozen=True)
class PaginatedSessions:
    items: list[SessionDetail]
    page: int
    page_size: int
    total: int


@dataclass(frozen=True)
class BulkSessionResult:
    sessions_created: int
    sessions_skipped: int
    skipped_reasons: list[str] = field(default_factory=list)


def _to_detail(session: Session) -> SessionDetail:
    return SessionDetail(
        id=session.id,
        client_id=session.client_id,
        trainer_id=session.trainer_id,
        scheduled_start=session.scheduled_start,
        scheduled_end=session.scheduled_end,
        duration_minutes=session.duration_minutes,
        status=session.status,
        meeting_type=session.meeting_type,
        meeting_link=session.meeting_link,
        trainer_notes=session.trainer_notes,
        trainer_feedback=session.trainer_feedback,
        homework=session.homework,
        next_session_focus=session.next_session_focus,
        attendance_status=session.attendance_status,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


class SessionService:
    """Business logic for coaching sessions and their Version-1 RBAC rules (Task-17.2).

    Sessions are never auto-generated: a SUPER_ADMIN or TRAINER explicitly
    schedules each one (individually or via bulk date-range expansion).
    TRAINER may only act as themselves and only for clients assigned to them;
    SUPER_ADMIN may act as an override for any assigned trainer/client pair.
    CLIENT is read-only and may only see their own sessions.
    """

    def __init__(
        self,
        session_repository: SessionRepository,
        client_repository: ClientRepository,
        assignment_repository: AssignmentRepository,
        subscription_repository: SubscriptionRepository,
        subscription_plan_repository: SubscriptionPlanRepository,
    ) -> None:
        self._session_repository = session_repository
        self._client_repository = client_repository
        self._assignment_repository = assignment_repository
        self._subscription_repository = subscription_repository
        self._subscription_plan_repository = subscription_plan_repository

    async def _resolve_trainer_id(
        self, actor_role: str | None, actor_id: uuid.UUID, requested_trainer_id: uuid.UUID | None
    ) -> uuid.UUID:
        if actor_role == RoleName.TRAINER:
            own_trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
            if own_trainer_id is None:
                raise TrainerNotFoundError("No trainer profile exists for the current user.")
            if requested_trainer_id is not None and requested_trainer_id != own_trainer_id:
                raise ForbiddenError("Trainers may only create sessions for themselves.")
            return own_trainer_id

        if requested_trainer_id is None:
            raise TrainerNotFoundError("trainer_id is required.")
        return requested_trainer_id

    async def remaining_sessions(self, client_id: uuid.UUID) -> int | None:
        """Sessions still available on the client's active subscription plan.

        Returns None when the plan has no configured limit (unlimited sessions).
        """
        subscription = await self._subscription_repository.get_active_for_client(client_id)
        if subscription is None:
            return 0

        plan = await self._subscription_plan_repository.get_by_id(
            subscription.subscription_plan_id
        )
        if plan is None or plan.max_sessions_per_month is None:
            return None

        used = await self._session_repository.count_active_for_client(client_id)
        return max(plan.max_sessions_per_month - used, 0)

    async def _ensure_client_eligible(self, client_id: uuid.UUID) -> None:
        subscription = await self._subscription_repository.get_active_for_client(client_id)
        if subscription is None or not can_schedule_sessions(subscription):
            raise SubscriptionNotEligibleError(
                f"Client '{client_id}' does not have a subscription eligible for scheduling."
            )

    async def _can_schedule_session(
        self,
        client_id: uuid.UUID,
        trainer_id: uuid.UUID,
        scheduled_start: datetime,
        scheduled_end: datetime,
    ) -> None:
        if scheduled_start < datetime.now(timezone.utc):
            raise SessionInPastError("Sessions cannot be scheduled in the past.")

        if await self._session_repository.client_has_overlap(
            client_id, scheduled_start, scheduled_end
        ):
            raise ClientOverlapError(
                f"Client has an overlapping session on {scheduled_start.date()}."
            )

        if await self._session_repository.trainer_has_overlap(
            trainer_id, scheduled_start, scheduled_end
        ):
            raise TrainerOverlapError(
                f"Trainer has an overlapping session on {scheduled_start.date()}."
            )

        remaining = await self.remaining_sessions(client_id)
        if remaining is not None and remaining <= 0:
            raise SessionLimitReachedError(
                "Client has reached the maximum number of sessions for this subscription."
            )

    async def _validate_session_request(
        self,
        actor_role: str | None,
        actor_id: uuid.UUID,
        client_id: uuid.UUID,
        trainer_id: uuid.UUID | None,
    ) -> uuid.UUID:
        if actor_role not in (RoleName.SUPER_ADMIN, RoleName.TRAINER):
            raise ForbiddenError("Only Trainers and Super Admins may create sessions.")

        if await self._client_repository.get_by_id(client_id) is None:
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")

        effective_trainer_id = await self._resolve_trainer_id(actor_role, actor_id, trainer_id)
        if not await self._assignment_repository.trainer_exists(effective_trainer_id):
            raise TrainerNotFoundError(f"Trainer '{effective_trainer_id}' was not found.")

        if not await self._assignment_repository.exists_for_pair(client_id, effective_trainer_id):
            raise TrainerNotAssignedError(f"Trainer is not assigned to client '{client_id}'.")

        await self._ensure_client_eligible(client_id)
        return effective_trainer_id

    async def create_session(
        self,
        actor_role: str | None,
        actor_id: uuid.UUID,
        client_id: uuid.UUID,
        trainer_id: uuid.UUID | None,
        scheduled_start: datetime,
        duration_minutes: int,
        meeting_type: SessionMeetingType,
        meeting_link: str | None,
        trainer_notes: str | None,
    ) -> SessionDetail:
        effective_trainer_id = await self._validate_session_request(
            actor_role, actor_id, client_id, trainer_id
        )

        scheduled_end = scheduled_start + timedelta(minutes=duration_minutes)
        await self._can_schedule_session(
            client_id, effective_trainer_id, scheduled_start, scheduled_end
        )

        session = await self._session_repository.create(
            Session(
                client_id=client_id,
                trainer_id=effective_trainer_id,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                duration_minutes=duration_minutes,
                status=SessionStatus.SCHEDULED,
                meeting_type=meeting_type,
                meeting_link=meeting_link,
                trainer_notes=trainer_notes,
            )
        )
        return _to_detail(session)

    async def bulk_create_sessions(
        self,
        actor_role: str | None,
        actor_id: uuid.UUID,
        client_id: uuid.UUID,
        trainer_id: uuid.UUID | None,
        start_date: date,
        end_date: date,
        days: list[str],
        start_time: time,
        duration_minutes: int,
        meeting_type: SessionMeetingType,
    ) -> BulkSessionResult:
        effective_trainer_id = await self._validate_session_request(
            actor_role, actor_id, client_id, trainer_id
        )

        created = 0
        skipped = 0
        reasons: list[str] = []
        for slot_start in generate_bulk_session_starts(start_date, end_date, days, start_time):
            slot_end = slot_start + timedelta(minutes=duration_minutes)
            try:
                await self._can_schedule_session(
                    client_id, effective_trainer_id, slot_start, slot_end
                )
            except (
                SessionInPastError,
                ClientOverlapError,
                TrainerOverlapError,
                SessionLimitReachedError,
            ) as exc:
                skipped += 1
                reasons.append(str(exc))
                continue

            await self._session_repository.create(
                Session(
                    client_id=client_id,
                    trainer_id=effective_trainer_id,
                    scheduled_start=slot_start,
                    scheduled_end=slot_end,
                    duration_minutes=duration_minutes,
                    status=SessionStatus.SCHEDULED,
                    meeting_type=meeting_type,
                )
            )
            created += 1

        return BulkSessionResult(
            sessions_created=created, sessions_skipped=skipped, skipped_reasons=reasons
        )

    async def list_sessions(
        self, actor_role: str | None, actor_id: uuid.UUID, page: int, page_size: int
    ) -> PaginatedSessions:
        offset = (page - 1) * page_size

        if actor_role == RoleName.SUPER_ADMIN:
            sessions, total = await self._session_repository.list_paginated(offset, page_size)
        elif actor_role == RoleName.TRAINER:
            trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
            if trainer_id is None:
                raise TrainerNotFoundError("No trainer profile exists for the current user.")
            sessions, total = await self._session_repository.list_for_trainer(
                trainer_id, offset, page_size
            )
        elif actor_role == RoleName.CLIENT:
            client_record = await self._client_repository.get_by_user_id(actor_id)
            if client_record is None:
                raise ClientNotFoundError("No client profile exists for the current user.")
            sessions, total = await self._session_repository.list_for_client(
                client_record.client.id, offset, page_size
            )
        else:
            raise ForbiddenError("Not authorized to list sessions.")

        return PaginatedSessions(
            items=[_to_detail(session) for session in sessions],
            page=page,
            page_size=page_size,
            total=total,
        )

    async def list_my_sessions(
        self, actor_role: str | None, actor_id: uuid.UUID
    ) -> list[SessionDetail]:
        if actor_role != RoleName.CLIENT:
            raise ForbiddenError("Only Clients may view their own sessions.")

        client_record = await self._client_repository.get_by_user_id(actor_id)
        if client_record is None:
            raise ClientNotFoundError("No client profile exists for the current user.")

        sessions = await self._session_repository.list_all_for_client(client_record.client.id)
        return [_to_detail(session) for session in sessions]

    async def get_session(
        self, actor_role: str | None, actor_id: uuid.UUID, session_id: uuid.UUID
    ) -> SessionDetail:
        session = await self._session_repository.get_by_id(session_id)
        if session is None:
            raise SessionNotFoundError(f"Session '{session_id}' was not found.")

        if actor_role == RoleName.SUPER_ADMIN:
            pass
        elif actor_role == RoleName.TRAINER:
            trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
            if trainer_id is None or session.trainer_id != trainer_id:
                raise ForbiddenError("Trainers may only view their own sessions.")
        elif actor_role == RoleName.CLIENT:
            client_record = await self._client_repository.get_by_user_id(actor_id)
            if client_record is None or session.client_id != client_record.client.id:
                raise ForbiddenError("Clients may only view their own sessions.")
        else:
            raise ForbiddenError("Not authorized to view sessions.")

        return _to_detail(session)

    async def update_session(
        self, actor_role: str | None, actor_id: uuid.UUID, session_id: uuid.UUID, values: dict
    ) -> SessionDetail:
        if actor_role not in (RoleName.SUPER_ADMIN, RoleName.TRAINER):
            raise ForbiddenError("Only Trainers and Super Admins may update sessions.")

        session = await self._session_repository.get_by_id(session_id)
        if session is None:
            raise SessionNotFoundError(f"Session '{session_id}' was not found.")

        if actor_role == RoleName.TRAINER:
            trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
            if trainer_id is None or session.trainer_id != trainer_id:
                raise ForbiddenError("Trainers may only update their own sessions.")

        if "attendance_status" in values:
            self._ensure_attendance_mutable(session)

        updated = await self._session_repository.update(session_id, values)
        return _to_detail(updated)

    def _ensure_attendance_mutable(self, session: Session) -> None:
        if session.status == SessionStatus.COMPLETED:
            raise AttendanceImmutableError(
                "Attendance cannot be changed once the session is marked COMPLETED."
            )

    async def _authorize_trainer_write(
        self, actor_role: str | None, actor_id: uuid.UUID, session: Session
    ) -> None:
        if actor_role not in (RoleName.SUPER_ADMIN, RoleName.TRAINER):
            raise ForbiddenError("Only Trainers and Super Admins may perform this action.")
        if actor_role == RoleName.TRAINER:
            trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
            if trainer_id is None or session.trainer_id != trainer_id:
                raise ForbiddenError("Trainers may only manage their own assigned sessions.")

    async def update_session_notes(
        self, actor_role: str | None, actor_id: uuid.UUID, session_id: uuid.UUID, values: dict
    ) -> SessionDetail:
        if actor_role not in (RoleName.SUPER_ADMIN, RoleName.TRAINER):
            raise ForbiddenError("Only Trainers and Super Admins may update session notes.")

        session = await self._session_repository.get_by_id(session_id)
        if session is None:
            raise SessionNotFoundError(f"Session '{session_id}' was not found.")

        await self._authorize_trainer_write(actor_role, actor_id, session)

        updated = await self._session_repository.update(session_id, values)
        return _to_detail(updated)

    async def update_session_attendance(
        self,
        actor_role: str | None,
        actor_id: uuid.UUID,
        session_id: uuid.UUID,
        attendance_status: SessionAttendanceStatus,
    ) -> SessionDetail:
        session = await self._session_repository.get_by_id(session_id)
        if session is None:
            raise SessionNotFoundError(f"Session '{session_id}' was not found.")

        await self._authorize_trainer_write(actor_role, actor_id, session)
        self._ensure_attendance_mutable(session)

        updated = await self._session_repository.update(
            session_id, {"attendance_status": attendance_status}
        )
        return _to_detail(updated)

    async def get_session_summary(
        self, actor_role: str | None, actor_id: uuid.UUID, session_id: uuid.UUID
    ) -> dict:
        session = await self._session_repository.get_by_id(session_id)
        if session is None:
            raise SessionNotFoundError(f"Session '{session_id}' was not found.")

        if actor_role == RoleName.SUPER_ADMIN:
            pass
        elif actor_role == RoleName.TRAINER:
            trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
            if trainer_id is None or session.trainer_id != trainer_id:
                raise ForbiddenError("Trainers may only view their own sessions.")
        elif actor_role == RoleName.CLIENT:
            client_record = await self._client_repository.get_by_user_id(actor_id)
            if client_record is None or session.client_id != client_record.client.id:
                raise ForbiddenError("Clients may only view their own sessions.")
        else:
            raise ForbiddenError("Not authorized to view sessions.")

        session_date = await self._session_date(session)
        attendance_status = session.attendance_status.value if session.attendance_status else None

        if actor_role == RoleName.CLIENT:
            return {
                "session_date": session_date,
                "attendance_status": attendance_status,
                "homework": session.homework,
            }

        return {
            "session_date": session_date,
            "attendance_status": attendance_status,
            "trainer_notes": session.trainer_notes,
            "trainer_feedback": session.trainer_feedback,
            "homework": session.homework,
            "next_session_focus": session.next_session_focus,
        }

    async def _session_date(self, session: Session) -> str:
        """The calendar date of a session, per the owning client's IANA timezone.

        Per TIMEZONE_REQUIREMENTS.md the client's timezone is the source of
        truth for scheduling, so it (not the viewer's timezone) determines
        which calendar date a session falls on.
        """
        client_record = await self._client_repository.get_by_id(session.client_id)
        if client_record is None:
            return session.scheduled_start.date().isoformat()
        local_start = session.scheduled_start.astimezone(ZoneInfo(client_record.client.timezone))
        return local_start.date().isoformat()
