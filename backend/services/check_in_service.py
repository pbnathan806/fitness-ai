import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from core.constants import RoleName
from models.check_in import CheckIn
from models.session import SessionStatus
from repositories.assignment_repository import AssignmentRepository
from repositories.check_in_repository import CheckInRepository
from repositories.client_repository import ClientRepository
from repositories.session_repository import SessionRepository
from services.application_setting_service import ApplicationSettingService
from utils.check_in import CHECK_IN_FIELDS, at_least_one_checkin_field_required


class ForbiddenError(Exception):
    """Raised when the acting user's role does not permit the requested action."""


class ClientNotFoundError(Exception):
    """Raised when no client profile exists for the requested identifier."""


class TrainerNotFoundError(Exception):
    """Raised when no trainer profile exists for the current user."""


class TrainerNotAssignedError(Exception):
    """Raised when the resolved trainer is not assigned to the requested client."""


class CheckInFieldsRequiredError(Exception):
    """Raised when a request would leave a check-in with no populated fields."""


class DuplicateCheckInError(Exception):
    """Raised when the target session already has a check-in."""


class CheckInNotFoundError(Exception):
    """Raised when no check-in exists for the requested identifier/session."""


class SessionNotFoundError(Exception):
    """Raised when no session exists for the requested identifier."""


class SessionCancelledError(Exception):
    """Raised when a check-in is attempted against a CANCELLED session."""


class SessionNotStartedError(Exception):
    """Raised when a check-in is attempted before the session has started."""


class CheckInEditWindowExpiredError(Exception):
    """Raised when a check-in edit is attempted after the configured edit window."""


@dataclass(frozen=True)
class CheckInDetail:
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


@dataclass(frozen=True)
class PaginatedCheckIns:
    items: list[CheckInDetail]
    page: int
    page_size: int
    total: int


@dataclass(frozen=True)
class PendingCheckInDetail:
    session_id: uuid.UUID
    client_id: uuid.UUID
    client_name: str
    scheduled_start: datetime
    days_pending: int


def _to_detail(check_in: CheckIn) -> CheckInDetail:
    return CheckInDetail(
        id=check_in.id,
        session_id=check_in.session_id,
        client_id=check_in.client_id,
        sleep_hours=check_in.sleep_hours,
        water_intake_liters=check_in.water_intake_liters,
        energy_level=check_in.energy_level,
        mood=check_in.mood,
        workout_completed=check_in.workout_completed,
        diet_followed=check_in.diet_followed,
        notes=check_in.notes,
        submitted_by=check_in.submitted_by,
        submitted_at=check_in.submitted_at,
        created_at=check_in.created_at,
        updated_at=check_in.updated_at,
    )


class CheckInService:
    """Business logic for session-centric client wellness check-ins (Check-ins V2).

    A Check-in belongs to exactly one Session and represents the client's
    progress since the previous coaching session. CLIENT, assigned TRAINER,
    and SUPER_ADMIN may submit or edit a check-in (retroactively, since
    trainers frequently forget to enter them right after a session), but
    edits are only allowed until check_in_edit_window_days after
    Session.scheduled_start.
    """

    def __init__(
        self,
        check_in_repository: CheckInRepository,
        client_repository: ClientRepository,
        assignment_repository: AssignmentRepository,
        session_repository: SessionRepository,
        application_setting_service: ApplicationSettingService,
    ) -> None:
        self._check_in_repository = check_in_repository
        self._client_repository = client_repository
        self._assignment_repository = assignment_repository
        self._session_repository = session_repository
        self._application_setting_service = application_setting_service

    async def _authorize(
        self, actor_role: str | None, actor_id: uuid.UUID, client_id: uuid.UUID
    ) -> None:
        if actor_role == RoleName.SUPER_ADMIN:
            return
        if actor_role == RoleName.TRAINER:
            trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
            if trainer_id is None or not await self._assignment_repository.exists_for_pair(
                client_id, trainer_id
            ):
                raise ForbiddenError("Trainers may only access check-ins for assigned clients.")
            return
        if actor_role == RoleName.CLIENT:
            client_record = await self._client_repository.get_by_user_id(actor_id)
            if client_record is None or client_record.client.id != client_id:
                raise ForbiddenError("Clients may only access their own check-ins.")
            return
        raise ForbiddenError("Not authorized to access check-ins.")

    async def create_check_in(
        self,
        actor_role: str | None,
        actor_id: uuid.UUID,
        session_id: uuid.UUID,
        sleep_hours: float | None,
        water_intake_liters: float | None,
        energy_level: int | None,
        mood: int | None,
        workout_completed: bool | None,
        diet_followed: bool | None,
        notes: str | None,
    ) -> CheckInDetail:
        session = await self._session_repository.get_by_id(session_id)
        if session is None:
            raise SessionNotFoundError(f"Session '{session_id}' was not found.")

        if actor_role == RoleName.TRAINER:
            trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
            if trainer_id is None:
                raise TrainerNotFoundError("No trainer profile exists for the current user.")
            if not await self._assignment_repository.exists_for_pair(
                session.client_id, trainer_id
            ):
                raise TrainerNotAssignedError(
                    f"Trainer is not assigned to client '{session.client_id}'."
                )
        else:
            await self._authorize(actor_role, actor_id, session.client_id)

        if session.status == SessionStatus.CANCELLED:
            raise SessionCancelledError("Cannot submit a check-in for a cancelled session.")

        if session.scheduled_start >= datetime.now(timezone.utc):
            raise SessionNotStartedError(
                "Cannot submit a check-in before the session has started."
            )

        if await self._check_in_repository.get_by_session_id(session_id) is not None:
            raise DuplicateCheckInError(f"A check-in already exists for session '{session_id}'.")

        values = {
            "sleep_hours": sleep_hours,
            "water_intake_liters": water_intake_liters,
            "energy_level": energy_level,
            "mood": mood,
            "workout_completed": workout_completed,
            "diet_followed": diet_followed,
            "notes": notes,
        }
        if not at_least_one_checkin_field_required(values):
            raise CheckInFieldsRequiredError("At least one check-in field must be provided.")

        check_in = await self._check_in_repository.create(
            CheckIn(
                session_id=session_id,
                client_id=session.client_id,
                submitted_by=actor_id,
                submitted_at=datetime.now(timezone.utc),
                **values,
            )
        )
        return _to_detail(check_in)

    async def update_check_in(
        self,
        actor_role: str | None,
        actor_id: uuid.UUID,
        check_in_id: uuid.UUID,
        values: dict,
    ) -> CheckInDetail:
        check_in = await self._check_in_repository.get_by_id(check_in_id)
        if check_in is None:
            raise CheckInNotFoundError(f"Check-in '{check_in_id}' was not found.")

        await self._authorize(actor_role, actor_id, check_in.client_id)

        # session_id is a NOT NULL FK with no delete path for sessions, so the
        # referenced Session always exists.
        session = await self._session_repository.get_by_id(check_in.session_id)
        edit_window_days = await self._application_setting_service.get_int(
            "check_in_edit_window_days"
        )
        deadline = session.scheduled_start + timedelta(days=edit_window_days)
        if datetime.now(timezone.utc) > deadline:
            raise CheckInEditWindowExpiredError(
                "This check-in can no longer be modified. The configured edit window "
                "has expired."
            )

        current_values = {field: getattr(check_in, field) for field in CHECK_IN_FIELDS}
        merged_values = {**current_values, **values}
        if not at_least_one_checkin_field_required(merged_values):
            raise CheckInFieldsRequiredError("At least one check-in field must be provided.")

        for field, value in values.items():
            setattr(check_in, field, value)

        updated = await self._check_in_repository.update(check_in)
        return _to_detail(updated)

    async def list_check_ins(
        self, actor_role: str | None, actor_id: uuid.UUID, page: int, page_size: int
    ) -> PaginatedCheckIns:
        offset = (page - 1) * page_size

        if actor_role == RoleName.SUPER_ADMIN:
            check_ins, total = await self._check_in_repository.list_paginated(offset, page_size)
        elif actor_role == RoleName.TRAINER:
            trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
            if trainer_id is None:
                raise TrainerNotFoundError("No trainer profile exists for the current user.")
            assigned_clients = await self._assignment_repository.list_clients_for_trainer(
                trainer_id
            )
            client_ids = [record.client.id for record in assigned_clients]
            check_ins, total = await self._check_in_repository.list_for_clients(
                client_ids, offset, page_size
            )
        elif actor_role == RoleName.CLIENT:
            client_record = await self._client_repository.get_by_user_id(actor_id)
            if client_record is None:
                raise ClientNotFoundError("No client profile exists for the current user.")
            check_ins, total = await self._check_in_repository.list_for_client(
                client_record.client.id, offset, page_size
            )
        else:
            raise ForbiddenError("Not authorized to list check-ins.")

        return PaginatedCheckIns(
            items=[_to_detail(check_in) for check_in in check_ins],
            page=page,
            page_size=page_size,
            total=total,
        )

    async def get_check_in(
        self, actor_role: str | None, actor_id: uuid.UUID, check_in_id: uuid.UUID
    ) -> CheckInDetail:
        check_in = await self._check_in_repository.get_by_id(check_in_id)
        if check_in is None:
            raise CheckInNotFoundError(f"Check-in '{check_in_id}' was not found.")

        await self._authorize(actor_role, actor_id, check_in.client_id)
        return _to_detail(check_in)

    async def get_check_in_by_session(
        self, actor_role: str | None, actor_id: uuid.UUID, session_id: uuid.UUID
    ) -> CheckInDetail:
        session = await self._session_repository.get_by_id(session_id)
        if session is None:
            raise SessionNotFoundError(f"Session '{session_id}' was not found.")

        await self._authorize(actor_role, actor_id, session.client_id)

        check_in = await self._check_in_repository.get_by_session_id(session_id)
        if check_in is None:
            raise CheckInNotFoundError(f"No check-in exists for session '{session_id}'.")
        return _to_detail(check_in)

    async def get_client_check_ins(
        self, actor_role: str | None, actor_id: uuid.UUID, client_id: uuid.UUID
    ) -> list[CheckInDetail]:
        if await self._client_repository.get_by_id(client_id) is None:
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")

        await self._authorize(actor_role, actor_id, client_id)

        check_ins = await self._check_in_repository.list_all_for_client(client_id)
        return [_to_detail(check_in) for check_in in check_ins]

    async def list_pending_check_ins(
        self, actor_role: str | None, actor_id: uuid.UUID
    ) -> list[PendingCheckInDetail]:
        if actor_role == RoleName.SUPER_ADMIN:
            client_ids = None
        elif actor_role == RoleName.TRAINER:
            trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
            if trainer_id is None:
                raise TrainerNotFoundError("No trainer profile exists for the current user.")
            assigned_clients = await self._assignment_repository.list_clients_for_trainer(
                trainer_id
            )
            client_ids = [record.client.id for record in assigned_clients]
        else:
            raise ForbiddenError("Not authorized to view pending check-ins.")

        now = datetime.now(timezone.utc)
        rows = await self._check_in_repository.list_pending(client_ids, now)
        return [
            PendingCheckInDetail(
                session_id=row.session_id,
                client_id=row.client_id,
                client_name=row.client_name,
                scheduled_start=row.scheduled_start,
                days_pending=(now - row.scheduled_start).days,
            )
            for row in rows
        ]
