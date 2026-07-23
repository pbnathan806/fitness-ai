import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from core.constants import RoleName
from models.check_in import CheckIn
from repositories.assignment_repository import AssignmentRepository
from repositories.check_in_repository import CheckInRepository
from repositories.client_repository import ClientRepository
from utils.check_in import (
    at_least_one_checkin_field_required,
    check_in_day_range_utc,
    one_check_in_per_client_per_day,
)


class ForbiddenError(Exception):
    """Raised when the acting user's role does not permit the requested action."""


class ClientNotFoundError(Exception):
    """Raised when no client profile exists for the requested identifier."""


class TrainerNotFoundError(Exception):
    """Raised when no trainer profile exists for the current user."""


class TrainerNotAssignedError(Exception):
    """Raised when the resolved trainer is not assigned to the requested client."""


class CheckInFieldsRequiredError(Exception):
    """Raised when a create request has no check-in fields populated."""


class DuplicateCheckInError(Exception):
    """Raised when a check-in already exists for the client on the target day."""


class CheckInNotFoundError(Exception):
    """Raised when no check-in exists for the requested identifier."""


@dataclass(frozen=True)
class CheckInDetail:
    id: uuid.UUID
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
class LatestCheckInDetail:
    sleep_hours: float | None
    water_intake_liters: float | None
    energy_level: int | None
    mood: int | None
    workout_completed: bool | None
    diet_followed: bool | None
    submitted_at: object


def _to_detail(check_in: CheckIn) -> CheckInDetail:
    return CheckInDetail(
        id=check_in.id,
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


def _to_latest_detail(check_in: CheckIn, client_timezone: str) -> LatestCheckInDetail:
    local_submitted_at = check_in.submitted_at.astimezone(ZoneInfo(client_timezone)).date()
    return LatestCheckInDetail(
        sleep_hours=check_in.sleep_hours,
        water_intake_liters=check_in.water_intake_liters,
        energy_level=check_in.energy_level,
        mood=check_in.mood,
        workout_completed=check_in.workout_completed,
        diet_followed=check_in.diet_followed,
        submitted_at=local_submitted_at,
    )


class CheckInService:
    """Business logic for daily client wellness check-ins and their RBAC rules (Task-19).

    Check-ins are immutable point-in-time snapshots: a SUPER_ADMIN, an
    assigned TRAINER, or the CLIENT themself may submit one, nothing about it
    is ever edited or removed, and only one may exist per client per
    calendar day (calendar day computed in the client's timezone).
    """

    def __init__(
        self,
        check_in_repository: CheckInRepository,
        client_repository: ClientRepository,
        assignment_repository: AssignmentRepository,
    ) -> None:
        self._check_in_repository = check_in_repository
        self._client_repository = client_repository
        self._assignment_repository = assignment_repository

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
        client_id: uuid.UUID,
        submitted_at: datetime | None,
        sleep_hours: float | None,
        water_intake_liters: float | None,
        energy_level: int | None,
        mood: int | None,
        workout_completed: bool | None,
        diet_followed: bool | None,
        notes: str | None,
    ) -> CheckInDetail:
        client_record = await self._client_repository.get_by_id(client_id)
        if client_record is None:
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")

        if actor_role == RoleName.TRAINER:
            trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
            if trainer_id is None:
                raise TrainerNotFoundError("No trainer profile exists for the current user.")
            if not await self._assignment_repository.exists_for_pair(client_id, trainer_id):
                raise TrainerNotAssignedError(f"Trainer is not assigned to client '{client_id}'.")
        else:
            await self._authorize(actor_role, actor_id, client_id)

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

        target_submitted_at = submitted_at or datetime.now(timezone.utc)
        client_timezone = client_record.client.timezone
        local_date = target_submitted_at.astimezone(ZoneInfo(client_timezone)).date()
        range_start, range_end = check_in_day_range_utc(local_date, client_timezone)

        existing = await self._check_in_repository.get_for_client_in_range(
            client_id, range_start, range_end
        )
        if not one_check_in_per_client_per_day(existing):
            raise DuplicateCheckInError("Check-in already exists for this date.")

        check_in = await self._check_in_repository.create(
            CheckIn(
                client_id=client_id,
                submitted_by=actor_id,
                submitted_at=target_submitted_at,
                **values,
            )
        )
        return _to_detail(check_in)

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

    async def get_client_check_ins(
        self, actor_role: str | None, actor_id: uuid.UUID, client_id: uuid.UUID
    ) -> list[CheckInDetail]:
        if await self._client_repository.get_by_id(client_id) is None:
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")

        await self._authorize(actor_role, actor_id, client_id)

        check_ins = await self._check_in_repository.list_all_for_client(client_id)
        return [_to_detail(check_in) for check_in in check_ins]

    async def get_latest_check_in(
        self, actor_role: str | None, actor_id: uuid.UUID, client_id: uuid.UUID
    ) -> LatestCheckInDetail:
        client_record = await self._client_repository.get_by_id(client_id)
        if client_record is None:
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")

        await self._authorize(actor_role, actor_id, client_id)

        check_ins = await self._check_in_repository.list_all_for_client(client_id)
        if not check_ins:
            raise CheckInNotFoundError(f"No check-ins recorded for client '{client_id}'.")

        return _to_latest_detail(check_ins[0], client_record.client.timezone)
