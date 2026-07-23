import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from core.constants import RoleName
from models.measurement import Measurement
from repositories.assignment_repository import AssignmentRepository
from repositories.client_repository import ClientRepository
from repositories.measurement_repository import MeasurementRepository
from utils.measurement import at_least_one_measurement_required


class ForbiddenError(Exception):
    """Raised when the acting user's role does not permit the requested action."""


class ClientNotFoundError(Exception):
    """Raised when no client profile exists for the requested identifier."""


class TrainerNotFoundError(Exception):
    """Raised when no trainer profile exists for the current user."""


class TrainerNotAssignedError(Exception):
    """Raised when the resolved trainer is not assigned to the requested client."""


class MeasurementFieldsRequiredError(Exception):
    """Raised when a create request has no measurement fields populated."""


class MeasurementNotFoundError(Exception):
    """Raised when no measurement exists for the requested identifier."""


@dataclass(frozen=True)
class MeasurementDetail:
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


@dataclass(frozen=True)
class PaginatedMeasurements:
    items: list[MeasurementDetail]
    page: int
    page_size: int
    total: int


@dataclass(frozen=True)
class LatestMeasurementDetail:
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


def _to_detail(measurement: Measurement) -> MeasurementDetail:
    return MeasurementDetail(
        id=measurement.id,
        client_id=measurement.client_id,
        weight_kg=measurement.weight_kg,
        body_fat_percentage=measurement.body_fat_percentage,
        chest_cm=measurement.chest_cm,
        waist_cm=measurement.waist_cm,
        hips_cm=measurement.hips_cm,
        left_arm_cm=measurement.left_arm_cm,
        right_arm_cm=measurement.right_arm_cm,
        left_thigh_cm=measurement.left_thigh_cm,
        right_thigh_cm=measurement.right_thigh_cm,
        resting_heart_rate=measurement.resting_heart_rate,
        recorded_by=measurement.recorded_by,
        recorded_at=measurement.recorded_at,
        created_at=measurement.created_at,
        updated_at=measurement.updated_at,
    )


def _change(current, previous):
    if current is None or previous is None:
        return None
    return current - previous


def _to_latest_detail(
    latest: Measurement, previous: Measurement | None, client_timezone: str
) -> LatestMeasurementDetail:
    def prev(field: str):
        return getattr(previous, field) if previous is not None else None

    local_recorded_at = latest.recorded_at.astimezone(ZoneInfo(client_timezone)).date()

    return LatestMeasurementDetail(
        weight_kg=latest.weight_kg,
        previous_weight_kg=prev("weight_kg"),
        weight_change=_change(latest.weight_kg, prev("weight_kg")),
        body_fat_percentage=latest.body_fat_percentage,
        previous_body_fat_percentage=prev("body_fat_percentage"),
        body_fat_change=_change(latest.body_fat_percentage, prev("body_fat_percentage")),
        chest_cm=latest.chest_cm,
        previous_chest_cm=prev("chest_cm"),
        chest_change=_change(latest.chest_cm, prev("chest_cm")),
        waist_cm=latest.waist_cm,
        previous_waist_cm=prev("waist_cm"),
        waist_change=_change(latest.waist_cm, prev("waist_cm")),
        hips_cm=latest.hips_cm,
        previous_hips_cm=prev("hips_cm"),
        hips_change=_change(latest.hips_cm, prev("hips_cm")),
        left_arm_cm=latest.left_arm_cm,
        previous_left_arm_cm=prev("left_arm_cm"),
        left_arm_change=_change(latest.left_arm_cm, prev("left_arm_cm")),
        right_arm_cm=latest.right_arm_cm,
        previous_right_arm_cm=prev("right_arm_cm"),
        right_arm_change=_change(latest.right_arm_cm, prev("right_arm_cm")),
        left_thigh_cm=latest.left_thigh_cm,
        previous_left_thigh_cm=prev("left_thigh_cm"),
        left_thigh_change=_change(latest.left_thigh_cm, prev("left_thigh_cm")),
        right_thigh_cm=latest.right_thigh_cm,
        previous_right_thigh_cm=prev("right_thigh_cm"),
        right_thigh_change=_change(latest.right_thigh_cm, prev("right_thigh_cm")),
        resting_heart_rate=latest.resting_heart_rate,
        previous_resting_heart_rate=prev("resting_heart_rate"),
        resting_heart_rate_change=_change(
            latest.resting_heart_rate, prev("resting_heart_rate")
        ),
        recorded_at=local_recorded_at,
    )


class MeasurementService:
    """Business logic for client body measurements and their RBAC rules (Task-18).

    Measurements are immutable point-in-time snapshots: a SUPER_ADMIN or
    assigned TRAINER records one, nothing about it is ever edited or removed,
    and CLIENT is strictly read-only over their own history.
    """

    def __init__(
        self,
        measurement_repository: MeasurementRepository,
        client_repository: ClientRepository,
        assignment_repository: AssignmentRepository,
    ) -> None:
        self._measurement_repository = measurement_repository
        self._client_repository = client_repository
        self._assignment_repository = assignment_repository

    async def _authorize_view(
        self, actor_role: str | None, actor_id: uuid.UUID, client_id: uuid.UUID
    ) -> None:
        if actor_role == RoleName.SUPER_ADMIN:
            return
        if actor_role == RoleName.TRAINER:
            trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
            if trainer_id is None or not await self._assignment_repository.exists_for_pair(
                client_id, trainer_id
            ):
                raise ForbiddenError("Trainers may only view measurements for assigned clients.")
            return
        if actor_role == RoleName.CLIENT:
            client_record = await self._client_repository.get_by_user_id(actor_id)
            if client_record is None or client_record.client.id != client_id:
                raise ForbiddenError("Clients may only view their own measurements.")
            return
        raise ForbiddenError("Not authorized to view measurements.")

    async def create_measurement(
        self,
        actor_role: str | None,
        actor_id: uuid.UUID,
        client_id: uuid.UUID,
        recorded_at: datetime | None,
        weight_kg: float | None,
        body_fat_percentage: float | None,
        chest_cm: float | None,
        waist_cm: float | None,
        hips_cm: float | None,
        left_arm_cm: float | None,
        right_arm_cm: float | None,
        left_thigh_cm: float | None,
        right_thigh_cm: float | None,
        resting_heart_rate: int | None,
    ) -> MeasurementDetail:
        if actor_role not in (RoleName.SUPER_ADMIN, RoleName.TRAINER):
            raise ForbiddenError("Only Trainers and Super Admins may record measurements.")

        if await self._client_repository.get_by_id(client_id) is None:
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")

        if actor_role == RoleName.TRAINER:
            trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
            if trainer_id is None:
                raise TrainerNotFoundError("No trainer profile exists for the current user.")
            if not await self._assignment_repository.exists_for_pair(client_id, trainer_id):
                raise TrainerNotAssignedError(f"Trainer is not assigned to client '{client_id}'.")

        values = {
            "weight_kg": weight_kg,
            "body_fat_percentage": body_fat_percentage,
            "chest_cm": chest_cm,
            "waist_cm": waist_cm,
            "hips_cm": hips_cm,
            "left_arm_cm": left_arm_cm,
            "right_arm_cm": right_arm_cm,
            "left_thigh_cm": left_thigh_cm,
            "right_thigh_cm": right_thigh_cm,
            "resting_heart_rate": resting_heart_rate,
        }
        if not at_least_one_measurement_required(values):
            raise MeasurementFieldsRequiredError(
                "At least one measurement field must be provided."
            )

        measurement = await self._measurement_repository.create(
            Measurement(
                client_id=client_id,
                recorded_by=actor_id,
                recorded_at=recorded_at or datetime.now(timezone.utc),
                **values,
            )
        )
        return _to_detail(measurement)

    async def list_measurements(
        self, actor_role: str | None, actor_id: uuid.UUID, page: int, page_size: int
    ) -> PaginatedMeasurements:
        offset = (page - 1) * page_size

        if actor_role == RoleName.SUPER_ADMIN:
            measurements, total = await self._measurement_repository.list_paginated(
                offset, page_size
            )
        elif actor_role == RoleName.TRAINER:
            trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
            if trainer_id is None:
                raise TrainerNotFoundError("No trainer profile exists for the current user.")
            assigned_clients = await self._assignment_repository.list_clients_for_trainer(
                trainer_id
            )
            client_ids = [record.client.id for record in assigned_clients]
            measurements, total = await self._measurement_repository.list_for_clients(
                client_ids, offset, page_size
            )
        elif actor_role == RoleName.CLIENT:
            client_record = await self._client_repository.get_by_user_id(actor_id)
            if client_record is None:
                raise ClientNotFoundError("No client profile exists for the current user.")
            measurements, total = await self._measurement_repository.list_for_client(
                client_record.client.id, offset, page_size
            )
        else:
            raise ForbiddenError("Not authorized to list measurements.")

        return PaginatedMeasurements(
            items=[_to_detail(measurement) for measurement in measurements],
            page=page,
            page_size=page_size,
            total=total,
        )

    async def get_measurement(
        self, actor_role: str | None, actor_id: uuid.UUID, measurement_id: uuid.UUID
    ) -> MeasurementDetail:
        measurement = await self._measurement_repository.get_by_id(measurement_id)
        if measurement is None:
            raise MeasurementNotFoundError(f"Measurement '{measurement_id}' was not found.")

        await self._authorize_view(actor_role, actor_id, measurement.client_id)
        return _to_detail(measurement)

    async def get_client_measurements(
        self, actor_role: str | None, actor_id: uuid.UUID, client_id: uuid.UUID
    ) -> list[MeasurementDetail]:
        if await self._client_repository.get_by_id(client_id) is None:
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")

        await self._authorize_view(actor_role, actor_id, client_id)

        measurements = await self._measurement_repository.list_all_for_client(client_id)
        return [_to_detail(measurement) for measurement in measurements]

    async def get_latest_measurement(
        self, actor_role: str | None, actor_id: uuid.UUID, client_id: uuid.UUID
    ) -> LatestMeasurementDetail:
        client_record = await self._client_repository.get_by_id(client_id)
        if client_record is None:
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")

        await self._authorize_view(actor_role, actor_id, client_id)

        measurements = await self._measurement_repository.list_all_for_client(client_id)
        if not measurements:
            raise MeasurementNotFoundError(f"No measurements recorded for client '{client_id}'.")

        latest = measurements[0]
        previous = measurements[1] if len(measurements) > 1 else None
        return _to_latest_detail(latest, previous, client_record.client.timezone)
