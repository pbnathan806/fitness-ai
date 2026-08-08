import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from core.constants import RoleName
from models.physical_assessment import PhysicalAssessment
from repositories.assignment_repository import AssignmentRepository
from repositories.client_repository import ClientRepository
from repositories.physical_assessment_repository import PhysicalAssessmentRepository
from repositories.trainer_repository import TrainerRepository
from services.application_setting_service import ApplicationSettingService
from utils.dashboard import client_local_today, is_physical_assessment_overdue
from utils.physical_assessment import (
    at_least_one_physical_assessment_required,
    PHYSICAL_ASSESSMENT_FIELDS,
)


class ForbiddenError(Exception):
    """Raised when the acting user's role does not permit the requested action."""


class ClientNotFoundError(Exception):
    """Raised when no client profile exists for the requested identifier."""


class TrainerNotFoundError(Exception):
    """Raised when no trainer profile exists for the current user."""


class TrainerNotAssignedError(Exception):
    """Raised when the resolved trainer is not assigned to the requested client."""


class PhysicalAssessmentFieldsRequiredError(Exception):
    """Raised when a create request has no physical assessment fields populated."""


class PhysicalAssessmentNotFoundError(Exception):
    """Raised when no physical assessment exists for the requested identifier."""


class PhysicalAssessmentEditWindowExpiredError(Exception):
    """Raised when a physical assessment edit is attempted after the configured edit window."""


@dataclass(frozen=True)
class PhysicalAssessmentDetail:
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
    front_photo_url: str | None
    back_photo_url: str | None
    side_photo_url: str | None
    recorded_by: uuid.UUID
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PaginatedPhysicalAssessments:
    items: list[PhysicalAssessmentDetail]
    page: int
    page_size: int
    total: int


@dataclass(frozen=True)
class LatestPhysicalAssessmentDetail:
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


@dataclass(frozen=True)
class PendingPhysicalAssessmentDetail:
    client_id: uuid.UUID
    client_name: str
    last_physical_assessment_date: date
    days_overdue: int


@dataclass(frozen=True)
class PendingPhysicalAssessments:
    """Wraps the pending list with the overdue threshold it was computed
    against, since TRAINER has no other way to read this application
    setting (GET /application-settings is SUPER_ADMIN-only). `timezone` is
    "Asia/Kolkata" for a SUPER_ADMIN caller, the caller's own profile
    timezone for a TRAINER caller."""

    items: list[PendingPhysicalAssessmentDetail]
    overdue_threshold_days: int
    timezone: str


def _to_detail(physical_assessment: PhysicalAssessment) -> PhysicalAssessmentDetail:
    return PhysicalAssessmentDetail(
        id=physical_assessment.id,
        client_id=physical_assessment.client_id,
        weight_kg=physical_assessment.weight_kg,
        body_fat_percentage=physical_assessment.body_fat_percentage,
        chest_cm=physical_assessment.chest_cm,
        waist_cm=physical_assessment.waist_cm,
        hips_cm=physical_assessment.hips_cm,
        left_arm_cm=physical_assessment.left_arm_cm,
        right_arm_cm=physical_assessment.right_arm_cm,
        left_thigh_cm=physical_assessment.left_thigh_cm,
        right_thigh_cm=physical_assessment.right_thigh_cm,
        resting_heart_rate=physical_assessment.resting_heart_rate,
        front_photo_url=physical_assessment.front_photo_url,
        back_photo_url=physical_assessment.back_photo_url,
        side_photo_url=physical_assessment.side_photo_url,
        recorded_by=physical_assessment.recorded_by,
        recorded_at=physical_assessment.recorded_at,
        created_at=physical_assessment.created_at,
        updated_at=physical_assessment.updated_at,
    )


def _change(current, previous):
    if current is None or previous is None:
        return None
    return current - previous


def _to_latest_detail(
    latest: PhysicalAssessment, previous: PhysicalAssessment | None, client_timezone: str
) -> LatestPhysicalAssessmentDetail:
    def prev(field: str):
        return getattr(previous, field) if previous is not None else None

    local_recorded_at = latest.recorded_at.astimezone(ZoneInfo(client_timezone)).date()

    return LatestPhysicalAssessmentDetail(
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


class PhysicalAssessmentService:
    """Business logic for client physical assessments and their RBAC rules
    (Task-18; renamed from Measurement/MeasurementService, shipped originally
    as "Measurements V1.1").

    Physical assessments are client-centric point-in-time snapshots, never
    tied to a Session or Subscription: a SUPER_ADMIN or assigned TRAINER
    records one and may edit it until physical_assessment_edit_window_days
    after recorded_at, and CLIENT is strictly read-only over their own
    history.
    """

    def __init__(
        self,
        physical_assessment_repository: PhysicalAssessmentRepository,
        client_repository: ClientRepository,
        assignment_repository: AssignmentRepository,
        application_setting_service: ApplicationSettingService,
        trainer_repository: TrainerRepository,
    ) -> None:
        self._physical_assessment_repository = physical_assessment_repository
        self._client_repository = client_repository
        self._assignment_repository = assignment_repository
        self._application_setting_service = application_setting_service
        self._trainer_repository = trainer_repository

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
                raise ForbiddenError("Trainers may only view physical assessments for assigned clients.")
            return
        if actor_role == RoleName.CLIENT:
            client_record = await self._client_repository.get_by_user_id(actor_id)
            if client_record is None or client_record.client.id != client_id:
                raise ForbiddenError("Clients may only view their own physical assessments.")
            return
        raise ForbiddenError("Not authorized to view physical assessments.")

    async def create_physical_assessment(
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
    ) -> PhysicalAssessmentDetail:
        if actor_role not in (RoleName.SUPER_ADMIN, RoleName.TRAINER):
            raise ForbiddenError("Only Trainers and Super Admins may record physical assessments.")

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
        if not at_least_one_physical_assessment_required(values):
            raise PhysicalAssessmentFieldsRequiredError(
                "At least one physical assessment field must be provided."
            )

        physical_assessment = await self._physical_assessment_repository.create(
            PhysicalAssessment(
                client_id=client_id,
                recorded_by=actor_id,
                recorded_at=recorded_at or datetime.now(timezone.utc),
                **values,
            )
        )
        return _to_detail(physical_assessment)

    async def update_physical_assessment(
        self,
        actor_role: str | None,
        actor_id: uuid.UUID,
        physical_assessment_id: uuid.UUID,
        values: dict,
    ) -> PhysicalAssessmentDetail:
        physical_assessment = await self._physical_assessment_repository.get_by_id(physical_assessment_id)
        if physical_assessment is None:
            raise PhysicalAssessmentNotFoundError(f"Physical assessment '{physical_assessment_id}' was not found.")

        if actor_role == RoleName.SUPER_ADMIN:
            pass
        elif actor_role == RoleName.TRAINER:
            trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
            if trainer_id is None:
                raise TrainerNotFoundError("No trainer profile exists for the current user.")
            if not await self._assignment_repository.exists_for_pair(
                physical_assessment.client_id, trainer_id
            ):
                raise TrainerNotAssignedError(
                    f"Trainer is not assigned to client '{physical_assessment.client_id}'."
                )
        else:
            raise ForbiddenError("Only Trainers and Super Admins may edit physical assessments.")

        edit_window_days = await self._application_setting_service.get_int(
            "physical_assessment_edit_window_days"
        )
        deadline = physical_assessment.recorded_at + timedelta(days=edit_window_days)
        if datetime.now(timezone.utc) > deadline:
            raise PhysicalAssessmentEditWindowExpiredError(
                "This physical assessment can no longer be modified. The configured edit window "
                "has expired."
            )

        current_values = {field: getattr(physical_assessment, field) for field in PHYSICAL_ASSESSMENT_FIELDS}
        merged_values = {**current_values, **values}
        if not at_least_one_physical_assessment_required(merged_values):
            raise PhysicalAssessmentFieldsRequiredError(
                "At least one physical assessment field must be provided."
            )

        for field, value in values.items():
            setattr(physical_assessment, field, value)

        updated = await self._physical_assessment_repository.update(physical_assessment)
        return _to_detail(updated)

    async def list_physical_assessments(
        self, actor_role: str | None, actor_id: uuid.UUID, page: int, page_size: int
    ) -> PaginatedPhysicalAssessments:
        offset = (page - 1) * page_size

        if actor_role == RoleName.SUPER_ADMIN:
            physical_assessments, total = await self._physical_assessment_repository.list_paginated(
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
            physical_assessments, total = await self._physical_assessment_repository.list_for_clients(
                client_ids, offset, page_size
            )
        elif actor_role == RoleName.CLIENT:
            client_record = await self._client_repository.get_by_user_id(actor_id)
            if client_record is None:
                raise ClientNotFoundError("No client profile exists for the current user.")
            physical_assessments, total = await self._physical_assessment_repository.list_for_client(
                client_record.client.id, offset, page_size
            )
        else:
            raise ForbiddenError("Not authorized to list physical assessments.")

        return PaginatedPhysicalAssessments(
            items=[_to_detail(physical_assessment) for physical_assessment in physical_assessments],
            page=page,
            page_size=page_size,
            total=total,
        )

    async def get_physical_assessment(
        self, actor_role: str | None, actor_id: uuid.UUID, physical_assessment_id: uuid.UUID
    ) -> PhysicalAssessmentDetail:
        physical_assessment = await self._physical_assessment_repository.get_by_id(physical_assessment_id)
        if physical_assessment is None:
            raise PhysicalAssessmentNotFoundError(f"Physical assessment '{physical_assessment_id}' was not found.")

        await self._authorize_view(actor_role, actor_id, physical_assessment.client_id)
        return _to_detail(physical_assessment)

    async def get_client_physical_assessments(
        self, actor_role: str | None, actor_id: uuid.UUID, client_id: uuid.UUID
    ) -> list[PhysicalAssessmentDetail]:
        if await self._client_repository.get_by_id(client_id) is None:
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")

        await self._authorize_view(actor_role, actor_id, client_id)

        physical_assessments = await self._physical_assessment_repository.list_all_for_client(client_id)
        return [_to_detail(physical_assessment) for physical_assessment in physical_assessments]

    async def get_latest_physical_assessment(
        self, actor_role: str | None, actor_id: uuid.UUID, client_id: uuid.UUID
    ) -> LatestPhysicalAssessmentDetail:
        client_record = await self._client_repository.get_by_id(client_id)
        if client_record is None:
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")

        await self._authorize_view(actor_role, actor_id, client_id)

        physical_assessments = await self._physical_assessment_repository.list_all_for_client(client_id)
        if not physical_assessments:
            raise PhysicalAssessmentNotFoundError(f"No physical assessments recorded for client '{client_id}'.")

        latest = physical_assessments[0]
        previous = physical_assessments[1] if len(physical_assessments) > 1 else None
        return _to_latest_detail(latest, previous, client_record.client.timezone)

    async def list_pending_physical_assessments(
        self, actor_role: str | None, actor_id: uuid.UUID
    ) -> PendingPhysicalAssessments:
        """SUPER_ADMIN sees every client's pending assessments, framed in the
        sitewide IST convention (no single trainer to anchor a personal
        timezone to). TRAINER sees only their own assigned clients, framed in
        their own profile timezone."""
        if actor_role == RoleName.SUPER_ADMIN:
            client_ids = None
            tz = "Asia/Kolkata"
        elif actor_role == RoleName.TRAINER:
            record = await self._trainer_repository.get_by_user_id(actor_id)
            if record is None:
                raise TrainerNotFoundError("No trainer profile exists for the current user.")
            assigned_clients = await self._assignment_repository.list_clients_for_trainer(
                record.trainer.id
            )
            client_ids = [client_record.client.id for client_record in assigned_clients]
            tz = record.trainer.timezone or "Asia/Kolkata"
        else:
            raise ForbiddenError("Not authorized to view pending physical assessments.")

        physical_assessment_overdue_days = await self._application_setting_service.get_int(
            "physical_assessment_overdue_days"
        )
        today = client_local_today(tz)
        rows = await self._physical_assessment_repository.list_latest_for_clients(client_ids)

        pending = []
        for row in rows:
            if not is_physical_assessment_overdue(
                row.recorded_at, today, physical_assessment_overdue_days, tz
            ):
                continue
            last_physical_assessment_date = row.recorded_at.astimezone(ZoneInfo(tz)).date()
            due_date = last_physical_assessment_date + timedelta(days=physical_assessment_overdue_days)
            pending.append(
                PendingPhysicalAssessmentDetail(
                    client_id=row.client_id,
                    client_name=row.client_name,
                    last_physical_assessment_date=last_physical_assessment_date,
                    days_overdue=(today - due_date).days,
                )
            )
        return PendingPhysicalAssessments(
            items=pending, overdue_threshold_days=physical_assessment_overdue_days, timezone=tz
        )
