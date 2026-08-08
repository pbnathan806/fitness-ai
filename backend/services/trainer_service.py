import uuid
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone

from zoneinfo import ZoneInfo

from core.constants import RoleName
from core.security import generate_temporary_password, hash_password
from models.session import SessionMeetingType, SessionStatus
from models.trainer_availability import TrainerAvailability
from models.trainer_profile import TrainerProfile
from repositories.assignment_repository import AssignmentRepository
from repositories.check_in_repository import CheckInRepository
from repositories.dashboard_repository import DashboardRepository
from repositories.physical_assessment_repository import PhysicalAssessmentRepository
from repositories.role_repository import RoleRepository
from repositories.session_repository import SessionRepository
from repositories.trainer_availability_repository import TrainerAvailabilityRepository
from repositories.trainer_repository import TrainerRecord, TrainerRepository
from repositories.user_repository import UserRepository
from services.application_setting_service import ApplicationSettingService
from utils.dashboard import (
    client_week_range_utc,
    ist_month_range_utc,
    ist_today_range_utc,
    is_physical_assessment_overdue,
    trainer_last_n_days_range_utc,
    trainer_today_and_tomorrow_range_utc,
)
from utils.subscription import current_india_date

_ADMIN_TIMEZONE = "Asia/Kolkata"
_CHECK_IN_RATE_WINDOW_DAYS = 90


class ForbiddenError(Exception):
    """Raised when the acting user's role does not permit the requested action."""


class TrainerNotFoundError(Exception):
    """Raised when no trainer profile exists for the requested identifier."""


class TrainerAlreadyExistsError(Exception):
    """Raised when attempting to create a trainer for an email already in use."""


class InvalidAvailabilityError(Exception):
    """Raised when an availability slot's fields are invalid (e.g. start_time >= end_time)."""


class AvailabilityOverlapError(Exception):
    """Raised when an availability slot overlaps an existing slot for the same trainer/weekday."""


class AvailabilityNotFoundError(Exception):
    """Raised when no availability slot exists for the requested identifier."""


@dataclass(frozen=True)
class TrainerProfileDetail:
    id: uuid.UUID
    first_name: str | None
    last_name: str | None
    email: str
    phone_number: str | None
    timezone: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class TrainerCreated:
    trainer: TrainerProfileDetail
    temporary_password: str


@dataclass(frozen=True)
class PaginatedTrainers:
    items: list[TrainerProfileDetail]
    page: int
    page_size: int
    total: int


@dataclass(frozen=True)
class TrainerSummary:
    assigned_clients: int
    sessions_this_week: int
    completed_sessions_this_month: int
    pending_check_ins: int
    pending_physical_assessments: int


@dataclass(frozen=True)
class TrainerPerformance:
    assigned_clients: int
    completed_sessions: int
    completion_rate: int
    average_check_in_rate: int


@dataclass(frozen=True)
class TrainerAvailabilityDetail:
    id: uuid.UUID
    trainer_id: uuid.UUID
    weekday: int
    start_time: time
    end_time: time
    is_available: bool
    created_at: datetime


@dataclass(frozen=True)
class TrainerAgendaSession:
    id: uuid.UUID
    client_id: uuid.UUID
    scheduled_start: datetime
    scheduled_end: datetime
    status: SessionStatus
    meeting_type: SessionMeetingType
    meeting_link: str | None
    day: str  # "today" | "tomorrow", relative to the trainer's own timezone


@dataclass(frozen=True)
class TrainerAgenda:
    timezone: str
    sessions: list[TrainerAgendaSession]


@dataclass(frozen=True)
class SessionNotesGapSession:
    id: uuid.UUID
    client_id: uuid.UUID
    scheduled_start: datetime
    scheduled_end: datetime
    status: SessionStatus
    meeting_type: SessionMeetingType


@dataclass(frozen=True)
class SessionNotesGap:
    gap_days: int
    timezone: str
    sessions: list[SessionNotesGapSession]


def _to_detail(record: TrainerRecord) -> TrainerProfileDetail:
    trainer = record.trainer
    return TrainerProfileDetail(
        id=trainer.id,
        first_name=trainer.first_name,
        last_name=trainer.last_name,
        email=record.email,
        phone_number=trainer.phone_number,
        timezone=trainer.timezone,
        is_active=bool(trainer.is_active) if trainer.is_active is not None else True,
        created_at=trainer.created_at,
        updated_at=trainer.updated_at,
    )


def _to_availability_detail(availability: TrainerAvailability) -> TrainerAvailabilityDetail:
    return TrainerAvailabilityDetail(
        id=availability.id,
        trainer_id=availability.trainer_id,
        weekday=availability.weekday,
        start_time=availability.start_time,
        end_time=availability.end_time,
        is_available=availability.is_available,
        created_at=availability.created_at,
    )


def _build_update_values(
    first_name: str | None,
    last_name: str | None,
    phone_number: str | None,
    timezone: str | None,
) -> dict:
    values: dict = {}
    if first_name is not None:
        values["first_name"] = first_name
    if last_name is not None:
        values["last_name"] = last_name
    if phone_number is not None:
        values["phone_number"] = phone_number
    if timezone is not None:
        values["timezone"] = timezone
    return values


class TrainerService:
    """Business logic for Trainer CRUD, self-profile, availability, summary and performance.

    SUPER_ADMIN has full access. TRAINER is restricted to its own profile and
    availability. CLIENT has no access to any endpoint in this module.
    """

    def __init__(
        self,
        trainer_repository: TrainerRepository,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        assignment_repository: AssignmentRepository,
        session_repository: SessionRepository,
        check_in_repository: CheckInRepository,
        physical_assessment_repository: PhysicalAssessmentRepository,
        trainer_availability_repository: TrainerAvailabilityRepository,
        dashboard_repository: DashboardRepository,
        application_setting_service: ApplicationSettingService,
    ) -> None:
        self._trainer_repository = trainer_repository
        self._user_repository = user_repository
        self._role_repository = role_repository
        self._assignment_repository = assignment_repository
        self._session_repository = session_repository
        self._check_in_repository = check_in_repository
        self._physical_assessment_repository = physical_assessment_repository
        self._trainer_availability_repository = trainer_availability_repository
        self._dashboard_repository = dashboard_repository
        self._application_setting_service = application_setting_service

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def list_trainers(
        self,
        actor_role: str | None,
        page: int,
        page_size: int,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        is_active: bool | None = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> PaginatedTrainers:
        if actor_role != RoleName.SUPER_ADMIN:
            raise ForbiddenError("Only Super Admins may list trainers.")

        offset = (page - 1) * page_size
        records, total = await self._trainer_repository.list_paginated(
            offset,
            page_size,
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_active=is_active,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )
        return PaginatedTrainers(
            items=[_to_detail(record) for record in records],
            page=page,
            page_size=page_size,
            total=total,
        )

    async def get_trainer(
        self, actor_role: str | None, actor_id: uuid.UUID, trainer_id: uuid.UUID
    ) -> TrainerProfileDetail:
        record = await self._trainer_repository.get_by_id(trainer_id)

        if actor_role == RoleName.SUPER_ADMIN:
            pass
        elif actor_role == RoleName.TRAINER:
            if record is None or record.trainer.user_id != actor_id:
                raise ForbiddenError("You do not have permission to access this trainer profile.")
        else:
            raise ForbiddenError("You do not have permission to access this trainer profile.")

        if record is None:
            raise TrainerNotFoundError(f"Trainer '{trainer_id}' was not found.")
        return _to_detail(record)

    async def create_trainer(
        self,
        actor_role: str | None,
        first_name: str,
        last_name: str,
        email: str,
        phone_number: str | None,
        timezone: str,
    ) -> TrainerCreated:
        if actor_role != RoleName.SUPER_ADMIN:
            raise ForbiddenError("Only Super Admins may create trainers.")

        existing_user = await self._user_repository.get_by_email(email)
        if existing_user is not None:
            raise TrainerAlreadyExistsError(f"A user with email '{email}' already exists.")

        trainer_role = await self._role_repository.get_by_name(RoleName.TRAINER)
        if trainer_role is None:
            raise RuntimeError("TRAINER role is not seeded in the database.")

        temporary_password = generate_temporary_password()
        user = await self._user_repository.create(
            email=email, password_hash=hash_password(temporary_password)
        )
        await self._role_repository.assign_role_to_user(user.id, trainer_role.id)

        trainer = await self._trainer_repository.create(
            TrainerProfile(
                user_id=user.id,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                timezone=timezone,
                is_active=True,
            )
        )
        detail = TrainerProfileDetail(
            id=trainer.id,
            first_name=trainer.first_name,
            last_name=trainer.last_name,
            email=user.email,
            phone_number=trainer.phone_number,
            timezone=trainer.timezone,
            is_active=True,
            created_at=trainer.created_at,
            updated_at=trainer.updated_at,
        )
        return TrainerCreated(trainer=detail, temporary_password=temporary_password)

    async def update_trainer(
        self,
        actor_role: str | None,
        actor_id: uuid.UUID,
        trainer_id: uuid.UUID,
        first_name: str | None,
        last_name: str | None,
        phone_number: str | None,
        timezone: str | None,
    ) -> TrainerProfileDetail:
        record = await self._trainer_repository.get_by_id(trainer_id)
        if record is None:
            raise TrainerNotFoundError(f"Trainer '{trainer_id}' was not found.")

        if actor_role == RoleName.SUPER_ADMIN:
            values = _build_update_values(first_name, last_name, phone_number, timezone)
        elif actor_role == RoleName.TRAINER:
            if record.trainer.user_id != actor_id:
                raise ForbiddenError("You may only update your own trainer profile.")
            if first_name is not None or last_name is not None:
                raise ForbiddenError("Trainers may only update phone_number and timezone.")
            values = _build_update_values(None, None, phone_number, timezone)
        else:
            raise ForbiddenError("You do not have permission to update this trainer profile.")

        updated = await self._trainer_repository.update(trainer_id, values)
        if updated is None:
            raise TrainerNotFoundError(f"Trainer '{trainer_id}' was not found.")
        return _to_detail(updated)

    async def update_status(
        self, actor_role: str | None, trainer_id: uuid.UUID, is_active: bool
    ) -> TrainerProfileDetail:
        if actor_role != RoleName.SUPER_ADMIN:
            raise ForbiddenError("Only Super Admins may change a trainer's status.")

        record = await self._trainer_repository.get_by_id(trainer_id)
        if record is None:
            raise TrainerNotFoundError(f"Trainer '{trainer_id}' was not found.")

        role_names = await self._role_repository.get_role_names_for_user(record.trainer.user_id)
        if RoleName.SUPER_ADMIN in role_names:
            raise ForbiddenError("Cannot deactivate a Super Admin.")

        updated = await self._trainer_repository.update(trainer_id, {"is_active": is_active})
        if updated is None:
            raise TrainerNotFoundError(f"Trainer '{trainer_id}' was not found.")
        return _to_detail(updated)

    # ------------------------------------------------------------------
    # Self profile
    # ------------------------------------------------------------------

    async def get_self(self, actor_role: str | None, actor_id: uuid.UUID) -> TrainerProfileDetail:
        if actor_role != RoleName.TRAINER:
            raise ForbiddenError("Only Trainers may access their own profile via /trainers/me.")

        record = await self._trainer_repository.get_by_user_id(actor_id)
        if record is None:
            raise TrainerNotFoundError("No trainer profile exists for the current user.")
        return _to_detail(record)

    async def update_self(
        self,
        actor_role: str | None,
        actor_id: uuid.UUID,
        phone_number: str | None,
        timezone: str | None,
    ) -> TrainerProfileDetail:
        if actor_role != RoleName.TRAINER:
            raise ForbiddenError("Only Trainers may update their own profile via /trainers/me.")

        record = await self._trainer_repository.get_by_user_id(actor_id)
        if record is None:
            raise TrainerNotFoundError("No trainer profile exists for the current user.")

        values = _build_update_values(None, None, phone_number, timezone)
        updated = await self._trainer_repository.update(record.trainer.id, values)
        if updated is None:
            raise TrainerNotFoundError("No trainer profile exists for the current user.")
        return _to_detail(updated)

    # ------------------------------------------------------------------
    # Summary / performance
    # ------------------------------------------------------------------

    async def _authorize_trainer_access(
        self, actor_role: str | None, actor_id: uuid.UUID, trainer_id: uuid.UUID
    ) -> None:
        if actor_role == RoleName.SUPER_ADMIN:
            return
        if actor_role == RoleName.TRAINER:
            record = await self._trainer_repository.get_by_id(trainer_id)
            if record is None or record.trainer.user_id != actor_id:
                raise ForbiddenError("You do not have permission to access this trainer's data.")
            return
        raise ForbiddenError("You do not have permission to access this trainer's data.")

    async def get_summary(
        self, actor_role: str | None, actor_id: uuid.UUID, trainer_id: uuid.UUID
    ) -> TrainerSummary:
        await self._authorize_trainer_access(actor_role, actor_id, trainer_id)

        if await self._trainer_repository.get_by_id(trainer_id) is None:
            raise TrainerNotFoundError(f"Trainer '{trainer_id}' was not found.")

        assigned = await self._assignment_repository.list_clients_for_trainer(trainer_id)
        client_ids = [record.client.id for record in assigned]

        week_start, week_end = client_week_range_utc(_ADMIN_TIMEZONE)
        month_start, month_end = ist_month_range_utc()
        today_start, today_end = ist_today_range_utc()
        now = datetime.now(timezone.utc)

        sessions_this_week = await self._session_repository.count_in_range(
            week_start, week_end, trainer_id=trainer_id, exclude_cancelled=True
        )
        completed_sessions_this_month = await self._session_repository.count_completed(
            trainer_id=trainer_id, start=month_start, end=month_end
        )

        pending_check_ins = await self._dashboard_repository.count_pending_check_ins(
            client_ids, today_start, today_end, now
        )

        physical_assessment_overdue_days = await self._application_setting_service.get_int(
            "physical_assessment_overdue_days"
        )
        # Clients with at least one physical assessment recorded; a client
        # never assessed at all is "missing", not "pending" - excluded here
        # so it isn't double-counted as overdue (matches the dashboards and
        # GET /physical-assessments/pending, which draw the same
        # distinction).
        latest_physical_assessments = (
            await self._physical_assessment_repository.get_latest_recorded_at_for_clients(
                client_ids
            )
        )
        today = current_india_date()
        pending_physical_assessments = sum(
            1
            for recorded_at in latest_physical_assessments.values()
            if is_physical_assessment_overdue(recorded_at, today, physical_assessment_overdue_days)
        )

        return TrainerSummary(
            assigned_clients=len(client_ids),
            sessions_this_week=sessions_this_week,
            completed_sessions_this_month=completed_sessions_this_month,
            pending_check_ins=pending_check_ins,
            pending_physical_assessments=pending_physical_assessments,
        )

    async def get_performance(
        self, actor_role: str | None, actor_id: uuid.UUID, trainer_id: uuid.UUID
    ) -> TrainerPerformance:
        await self._authorize_trainer_access(actor_role, actor_id, trainer_id)

        if await self._trainer_repository.get_by_id(trainer_id) is None:
            raise TrainerNotFoundError(f"Trainer '{trainer_id}' was not found.")

        assigned = await self._assignment_repository.list_clients_for_trainer(trainer_id)
        client_ids = [record.client.id for record in assigned]

        completed_sessions = await self._session_repository.count_completed(trainer_id=trainer_id)
        total_sessions = await self._session_repository.count_total(trainer_id=trainer_id)
        completion_rate = (
            round(completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
        )

        _, window_end = ist_today_range_utc()
        window_start = window_end - timedelta(days=_CHECK_IN_RATE_WINDOW_DAYS)

        submitted_check_ins = await self._check_in_repository.count_in_range(
            window_start, window_end, client_ids=client_ids
        )
        expected_check_ins = await self._session_repository.count_in_range(
            window_start, window_end, trainer_id=trainer_id, exclude_cancelled=True
        )
        average_check_in_rate = (
            round(submitted_check_ins / expected_check_ins * 100) if expected_check_ins > 0 else 0
        )

        return TrainerPerformance(
            assigned_clients=len(client_ids),
            completed_sessions=completed_sessions,
            completion_rate=completion_rate,
            average_check_in_rate=average_check_in_rate,
        )

    # ------------------------------------------------------------------
    # Agenda
    # ------------------------------------------------------------------

    async def get_agenda(self, actor_role: str | None, actor_id: uuid.UUID) -> TrainerAgenda:
        """Today & Tomorrow's sessions, framed in the trainer's own profile
        timezone (not the sitewide IST convention used elsewhere on this
        dashboard) per explicit product decision. See memory
        project_deferred_trainer_timezone_framing.
        """
        if actor_role != RoleName.TRAINER:
            raise ForbiddenError("Only Trainers may access their own agenda via /trainers/me/agenda.")

        record = await self._trainer_repository.get_by_user_id(actor_id)
        if record is None:
            raise TrainerNotFoundError("No trainer profile exists for the current user.")

        trainer_timezone = record.trainer.timezone or _ADMIN_TIMEZONE
        start, end = trainer_today_and_tomorrow_range_utc(trainer_timezone)
        today_local = datetime.now(ZoneInfo(trainer_timezone)).date()

        sessions = await self._session_repository.list_in_range(
            start, end, trainer_id=record.trainer.id, exclude_cancelled=True
        )

        return TrainerAgenda(
            timezone=trainer_timezone,
            sessions=[
                TrainerAgendaSession(
                    id=session.id,
                    client_id=session.client_id,
                    scheduled_start=session.scheduled_start,
                    scheduled_end=session.scheduled_end,
                    status=session.status,
                    meeting_type=session.meeting_type,
                    meeting_link=session.meeting_link,
                    day=(
                        "today"
                        if session.scheduled_start.astimezone(ZoneInfo(trainer_timezone)).date()
                        == today_local
                        else "tomorrow"
                    ),
                )
                for session in sessions
            ],
        )

    # ------------------------------------------------------------------
    # Session notes gap
    # ------------------------------------------------------------------

    async def get_session_notes_gap(
        self, actor_role: str | None, actor_id: uuid.UUID
    ) -> SessionNotesGap:
        """Past sessions in the trailing `session_notes_gap_days` days, framed in
        the trainer's own profile timezone, that are missing trainer_notes.
        """
        if actor_role != RoleName.TRAINER:
            raise ForbiddenError(
                "Only Trainers may access their own session notes gap via "
                "/trainers/me/session-notes-gap."
            )

        record = await self._trainer_repository.get_by_user_id(actor_id)
        if record is None:
            raise TrainerNotFoundError("No trainer profile exists for the current user.")

        trainer_timezone = record.trainer.timezone or _ADMIN_TIMEZONE
        gap_days = await self._application_setting_service.get_int("session_notes_gap_days")
        start, end = trainer_last_n_days_range_utc(trainer_timezone, gap_days)
        now = datetime.now(timezone.utc)

        sessions = await self._session_repository.list_in_range(
            start, end, trainer_id=record.trainer.id, exclude_cancelled=True
        )

        missing_notes = [
            session
            for session in sessions
            if session.scheduled_start < now and not (session.trainer_notes or "").strip()
        ]

        return SessionNotesGap(
            gap_days=gap_days,
            timezone=trainer_timezone,
            sessions=[
                SessionNotesGapSession(
                    id=session.id,
                    client_id=session.client_id,
                    scheduled_start=session.scheduled_start,
                    scheduled_end=session.scheduled_end,
                    status=session.status,
                    meeting_type=session.meeting_type,
                )
                for session in missing_notes
            ],
        )

    # ------------------------------------------------------------------
    # Availability
    # ------------------------------------------------------------------

    async def _get_own_trainer_id(self, actor_role: str | None, actor_id: uuid.UUID) -> uuid.UUID:
        if actor_role != RoleName.TRAINER:
            raise ForbiddenError("Only Trainers may manage their own availability.")

        record = await self._trainer_repository.get_by_user_id(actor_id)
        if record is None:
            raise TrainerNotFoundError("No trainer profile exists for the current user.")
        return record.trainer.id

    async def list_availability(
        self, actor_role: str | None, actor_id: uuid.UUID
    ) -> list[TrainerAvailabilityDetail]:
        trainer_id = await self._get_own_trainer_id(actor_role, actor_id)
        slots = await self._trainer_availability_repository.list_for_trainer(trainer_id)
        return [_to_availability_detail(slot) for slot in slots]

    async def get_availability(
        self, actor_role: str | None, actor_id: uuid.UUID, trainer_id: uuid.UUID
    ) -> list[TrainerAvailabilityDetail]:
        """Availability for an arbitrary trainer, e.g. so a SUPER_ADMIN can see a
        candidate trainer's weekly slots as context when assigning them to a
        client. Same RBAC shape as get_trainer: SUPER_ADMIN may view any
        trainer, a TRAINER may only view their own.
        """
        record = await self._trainer_repository.get_by_id(trainer_id)

        if actor_role == RoleName.SUPER_ADMIN:
            pass
        elif actor_role == RoleName.TRAINER:
            if record is None or record.trainer.user_id != actor_id:
                raise ForbiddenError("Trainers may only view their own availability.")
        else:
            raise ForbiddenError("You do not have permission to view this trainer's availability.")

        if record is None:
            raise TrainerNotFoundError(f"Trainer '{trainer_id}' was not found.")

        slots = await self._trainer_availability_repository.list_for_trainer(trainer_id)
        return [_to_availability_detail(slot) for slot in slots]

    async def create_availability(
        self,
        actor_role: str | None,
        actor_id: uuid.UUID,
        weekday: int,
        start_time: time,
        end_time: time,
        is_available: bool,
    ) -> TrainerAvailabilityDetail:
        trainer_id = await self._get_own_trainer_id(actor_role, actor_id)

        if start_time >= end_time:
            raise InvalidAvailabilityError("start_time must be before end_time.")

        overlap = await self._trainer_availability_repository.find_overlapping(
            trainer_id, weekday, start_time, end_time
        )
        if overlap is not None:
            raise AvailabilityOverlapError(
                "This slot overlaps an existing availability slot for the same weekday."
            )

        created = await self._trainer_availability_repository.create(
            TrainerAvailability(
                trainer_id=trainer_id,
                weekday=weekday,
                start_time=start_time,
                end_time=end_time,
                is_available=is_available,
            )
        )
        return _to_availability_detail(created)

    async def update_availability(
        self,
        actor_role: str | None,
        actor_id: uuid.UUID,
        availability_id: uuid.UUID,
        weekday: int,
        start_time: time,
        end_time: time,
        is_available: bool,
    ) -> TrainerAvailabilityDetail:
        trainer_id = await self._get_own_trainer_id(actor_role, actor_id)

        existing = await self._trainer_availability_repository.get_by_id(availability_id)
        if existing is None or existing.trainer_id != trainer_id:
            raise AvailabilityNotFoundError(f"Availability slot '{availability_id}' was not found.")

        if start_time >= end_time:
            raise InvalidAvailabilityError("start_time must be before end_time.")

        overlap = await self._trainer_availability_repository.find_overlapping(
            trainer_id, weekday, start_time, end_time, exclude_id=availability_id
        )
        if overlap is not None:
            raise AvailabilityOverlapError(
                "This slot overlaps an existing availability slot for the same weekday."
            )

        updated = await self._trainer_availability_repository.update(
            availability_id,
            {
                "weekday": weekday,
                "start_time": start_time,
                "end_time": end_time,
                "is_available": is_available,
            },
        )
        if updated is None:
            raise AvailabilityNotFoundError(f"Availability slot '{availability_id}' was not found.")
        return _to_availability_detail(updated)

    async def delete_availability(
        self, actor_role: str | None, actor_id: uuid.UUID, availability_id: uuid.UUID
    ) -> None:
        trainer_id = await self._get_own_trainer_id(actor_role, actor_id)

        existing = await self._trainer_availability_repository.get_by_id(availability_id)
        if existing is None or existing.trainer_id != trainer_id:
            raise AvailabilityNotFoundError(f"Availability slot '{availability_id}' was not found.")

        await self._trainer_availability_repository.delete(availability_id)
