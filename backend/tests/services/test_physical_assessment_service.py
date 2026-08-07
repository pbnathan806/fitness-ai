import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from core.constants import RoleName
from models.application_setting import ApplicationSetting
from models.client_trainer_assignment import ClientTrainerAssignment
from models.physical_assessment import PhysicalAssessment
from repositories.physical_assessment_repository import LatestPhysicalAssessmentRow, PhysicalAssessmentRepository
from services.application_setting_service import ApplicationSettingService
from services.physical_assessment_service import (
    ClientNotFoundError,
    ForbiddenError,
    PhysicalAssessmentEditWindowExpiredError,
    PhysicalAssessmentFieldsRequiredError,
    PhysicalAssessmentNotFoundError,
    PhysicalAssessmentService,
    TrainerNotAssignedError,
    TrainerNotFoundError,
)
from tests.services.test_application_setting_service import FakeApplicationSettingRepository
from tests.services.test_assignment_service import FakeAssignmentRepository, _make_trainer
from tests.services.test_client_service import FakeClientRepository, _make_client


class FakePhysicalAssessmentRepository(PhysicalAssessmentRepository):
    def __init__(self) -> None:
        self._physical_assessments: dict[uuid.UUID, PhysicalAssessment] = {}
        self._latest_rows: list[LatestPhysicalAssessmentRow] = []

    def seed(self, physical_assessment: PhysicalAssessment) -> None:
        self._physical_assessments[physical_assessment.id] = physical_assessment

    def seed_latest_row(self, row: LatestPhysicalAssessmentRow) -> None:
        self._latest_rows.append(row)

    async def create(self, physical_assessment: PhysicalAssessment) -> PhysicalAssessment:
        now = datetime.now(timezone.utc)
        physical_assessment.id = physical_assessment.id or uuid.uuid4()
        physical_assessment.created_at = now
        physical_assessment.updated_at = now
        self._physical_assessments[physical_assessment.id] = physical_assessment
        return physical_assessment

    async def update(self, physical_assessment: PhysicalAssessment) -> PhysicalAssessment:
        physical_assessment.updated_at = datetime.now(timezone.utc)
        return physical_assessment

    async def get_by_id(self, physical_assessment_id: uuid.UUID) -> PhysicalAssessment | None:
        return self._physical_assessments.get(physical_assessment_id)

    async def list_paginated(self, offset: int, limit: int) -> tuple[list[PhysicalAssessment], int]:
        ordered = sorted(
            self._physical_assessments.values(), key=lambda m: m.recorded_at, reverse=True
        )
        return ordered[offset : offset + limit], len(ordered)

    async def list_for_client(
        self, client_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[PhysicalAssessment], int]:
        matched = [m for m in self._physical_assessments.values() if m.client_id == client_id]
        ordered = sorted(matched, key=lambda m: m.recorded_at, reverse=True)
        return ordered[offset : offset + limit], len(ordered)

    async def list_for_clients(
        self, client_ids: list[uuid.UUID], offset: int, limit: int
    ) -> tuple[list[PhysicalAssessment], int]:
        matched = [m for m in self._physical_assessments.values() if m.client_id in client_ids]
        ordered = sorted(matched, key=lambda m: m.recorded_at, reverse=True)
        return ordered[offset : offset + limit], len(ordered)

    async def list_all_for_client(self, client_id: uuid.UUID) -> list[PhysicalAssessment]:
        matched = [m for m in self._physical_assessments.values() if m.client_id == client_id]
        return sorted(matched, key=lambda m: m.recorded_at, reverse=True)

    async def count_in_range(self, start: datetime, end: datetime) -> int:
        return sum(1 for m in self._physical_assessments.values() if start <= m.recorded_at < end)

    async def get_latest_recorded_at_for_clients(
        self, client_ids: list[uuid.UUID] | None = None
    ) -> dict[uuid.UUID, datetime]:
        latest: dict[uuid.UUID, datetime] = {}
        for m in self._physical_assessments.values():
            if client_ids is not None and m.client_id not in client_ids:
                continue
            if m.client_id not in latest or m.recorded_at > latest[m.client_id]:
                latest[m.client_id] = m.recorded_at
        return latest

    async def list_latest_for_clients(
        self, client_ids: list[uuid.UUID] | None
    ) -> list[LatestPhysicalAssessmentRow]:
        if client_ids is None:
            return list(self._latest_rows)
        return [row for row in self._latest_rows if row.client_id in client_ids]


def _make_physical_assessment(client_id: uuid.UUID, recorded_by: uuid.UUID, **overrides) -> PhysicalAssessment:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid.uuid4(),
        client_id=client_id,
        weight_kg=80,
        body_fat_percentage=None,
        chest_cm=None,
        waist_cm=92,
        hips_cm=None,
        left_arm_cm=None,
        right_arm_cm=None,
        left_thigh_cm=None,
        right_thigh_cm=None,
        resting_heart_rate=None,
        recorded_by=recorded_by,
        recorded_at=now,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return PhysicalAssessment(**defaults)


def _make_application_setting_service(
    physical_assessment_overdue_days: int = 14, edit_window_days: int = 30
) -> ApplicationSettingService:
    repository = FakeApplicationSettingRepository()
    now = datetime.now(timezone.utc)
    repository.seed(
        ApplicationSetting(
            id=uuid.uuid4(),
            key="physical_assessment_overdue_days",
            value=str(physical_assessment_overdue_days),
            description="Days after which physical_assessments are overdue.",
            created_at=now,
            updated_at=now,
        )
    )
    repository.seed(
        ApplicationSetting(
            id=uuid.uuid4(),
            key="physical_assessment_edit_window_days",
            value=str(edit_window_days),
            description="Edit window",
            created_at=now,
            updated_at=now,
        )
    )
    return ApplicationSettingService(repository)


def _make_service(
    physical_assessment_overdue_days: int = 14, edit_window_days: int = 30
) -> tuple[
    PhysicalAssessmentService, FakePhysicalAssessmentRepository, FakeClientRepository, FakeAssignmentRepository
]:
    physical_assessment_repository = FakePhysicalAssessmentRepository()
    client_repository = FakeClientRepository()
    assignment_repository = FakeAssignmentRepository()
    application_setting_service = _make_application_setting_service(
        physical_assessment_overdue_days, edit_window_days
    )
    service = PhysicalAssessmentService(
        physical_assessment_repository, client_repository, assignment_repository,
        application_setting_service,
    )
    return service, physical_assessment_repository, client_repository, assignment_repository


def _setup_assigned_pair(client_repository, assignment_repository):
    client = _make_client(user_id=uuid.uuid4())
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    client_repository.seed(client, "client@example.com")
    assignment_repository.seed_client(client)
    assignment_repository.seed_trainer(trainer)
    assignment_repository.seed_assignment(
        ClientTrainerAssignment(
            id=uuid.uuid4(), client_id=client.id, trainer_id=trainer.id, is_primary=True
        )
    )
    return client, trainer, trainer_user_id


def _create_kwargs(client_id: uuid.UUID, **overrides) -> dict:
    defaults = dict(
        client_id=client_id,
        recorded_at=None,
        weight_kg=None,
        body_fat_percentage=None,
        chest_cm=None,
        waist_cm=None,
        hips_cm=None,
        left_arm_cm=None,
        right_arm_cm=None,
        left_thigh_cm=None,
        right_thigh_cm=None,
        resting_heart_rate=None,
    )
    defaults.update(overrides)
    return defaults


# --- create_physical_assessment ------------------------------------------------------


def test_create_physical_assessment_with_weight_only_succeeds_for_super_admin():
    service, _, client_repository, assignment_repository = _make_service()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)

    detail = asyncio.run(
        service.create_physical_assessment(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            **_create_kwargs(client.id, weight_kg=80),
        )
    )

    assert detail.client_id == client.id
    assert detail.weight_kg == 80
    assert detail.body_fat_percentage is None


def test_create_physical_assessment_with_multiple_fields_succeeds():
    service, _, client_repository, assignment_repository = _make_service()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)

    detail = asyncio.run(
        service.create_physical_assessment(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            **_create_kwargs(
                client.id, weight_kg=80, body_fat_percentage=18, waist_cm=92
            ),
        )
    )

    assert detail.weight_kg == 80
    assert detail.body_fat_percentage == 18
    assert detail.waist_cm == 92


def test_create_physical_assessment_rejects_empty_payload():
    service, _, client_repository, assignment_repository = _make_service()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)

    with pytest.raises(PhysicalAssessmentFieldsRequiredError):
        asyncio.run(
            service.create_physical_assessment(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                **_create_kwargs(client.id),
            )
        )


def test_create_physical_assessment_succeeds_for_assigned_trainer():
    service, _, client_repository, assignment_repository = _make_service()
    client, trainer, trainer_user_id = _setup_assigned_pair(
        client_repository, assignment_repository
    )

    detail = asyncio.run(
        service.create_physical_assessment(
            actor_role=RoleName.TRAINER,
            actor_id=trainer_user_id,
            **_create_kwargs(client.id, weight_kg=75),
        )
    )

    assert detail.client_id == client.id
    assert detail.recorded_by == trainer_user_id


def test_create_physical_assessment_rejects_unassigned_trainer():
    service, _, client_repository, assignment_repository = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    # Note: no assignment created between trainer and client.

    with pytest.raises(TrainerNotAssignedError):
        asyncio.run(
            service.create_physical_assessment(
                actor_role=RoleName.TRAINER,
                actor_id=trainer_user_id,
                **_create_kwargs(client.id, weight_kg=75),
            )
        )


def test_create_physical_assessment_rejects_client_role():
    service, _, client_repository, assignment_repository = _make_service()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.create_physical_assessment(
                actor_role=RoleName.CLIENT,
                actor_id=uuid.uuid4(),
                **_create_kwargs(client.id, weight_kg=75),
            )
        )


def test_create_physical_assessment_raises_when_client_missing():
    service, *_ = _make_service()

    with pytest.raises(ClientNotFoundError):
        asyncio.run(
            service.create_physical_assessment(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                **_create_kwargs(uuid.uuid4(), weight_kg=75),
            )
        )


def test_create_physical_assessment_raises_when_trainer_profile_missing():
    service, _, client_repository, assignment_repository = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")

    with pytest.raises(TrainerNotFoundError):
        asyncio.run(
            service.create_physical_assessment(
                actor_role=RoleName.TRAINER,
                actor_id=uuid.uuid4(),
                **_create_kwargs(client.id, weight_kg=75),
            )
        )


# --- list_physical_assessments --------------------------------------------------------


def test_list_physical_assessments_returns_all_for_super_admin():
    service, physical_assessment_repository, *_ = _make_service()
    for _ in range(3):
        physical_assessment_repository.seed(_make_physical_assessment(uuid.uuid4(), uuid.uuid4()))

    result = asyncio.run(
        service.list_physical_assessments(
            actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), page=1, page_size=2
        )
    )

    assert result.total == 3
    assert len(result.items) == 2


def test_list_physical_assessments_returns_only_assigned_clients_for_trainer():
    service, physical_assessment_repository, client_repository, assignment_repository = _make_service()
    client, trainer, trainer_user_id = _setup_assigned_pair(
        client_repository, assignment_repository
    )
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(other_client, "other@example.com")
    physical_assessment_repository.seed(_make_physical_assessment(client.id, trainer.id))
    physical_assessment_repository.seed(_make_physical_assessment(other_client.id, uuid.uuid4()))

    result = asyncio.run(
        service.list_physical_assessments(
            actor_role=RoleName.TRAINER, actor_id=trainer_user_id, page=1, page_size=20
        )
    )

    assert result.total == 1
    assert result.items[0].client_id == client.id


def test_list_physical_assessments_returns_only_own_for_client():
    service, physical_assessment_repository, client_repository, _ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    physical_assessment_repository.seed(_make_physical_assessment(client.id, uuid.uuid4()))
    physical_assessment_repository.seed(_make_physical_assessment(other_client.id, uuid.uuid4()))

    result = asyncio.run(
        service.list_physical_assessments(
            actor_role=RoleName.CLIENT, actor_id=client_user_id, page=1, page_size=20
        )
    )

    assert result.total == 1
    assert result.items[0].client_id == client.id


# --- get_physical_assessment -----------------------------------------------------------


def test_get_physical_assessment_succeeds_for_owning_client():
    service, physical_assessment_repository, client_repository, _ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    client_repository.seed(client, "client@example.com")
    physical_assessment = _make_physical_assessment(client.id, uuid.uuid4())
    physical_assessment_repository.seed(physical_assessment)

    detail = asyncio.run(
        service.get_physical_assessment(
            actor_role=RoleName.CLIENT, actor_id=client_user_id, physical_assessment_id=physical_assessment.id
        )
    )

    assert detail.id == physical_assessment.id


def test_get_physical_assessment_rejects_non_owning_client():
    service, physical_assessment_repository, client_repository, _ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    client_repository.seed(client, "client@example.com")
    physical_assessment = _make_physical_assessment(uuid.uuid4(), uuid.uuid4())
    physical_assessment_repository.seed(physical_assessment)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_physical_assessment(
                actor_role=RoleName.CLIENT, actor_id=client_user_id, physical_assessment_id=physical_assessment.id
            )
        )


def test_get_physical_assessment_rejects_non_assigned_trainer():
    service, physical_assessment_repository, client_repository, assignment_repository = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    physical_assessment = _make_physical_assessment(uuid.uuid4(), uuid.uuid4())
    physical_assessment_repository.seed(physical_assessment)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_physical_assessment(
                actor_role=RoleName.TRAINER,
                actor_id=trainer_user_id,
                physical_assessment_id=physical_assessment.id,
            )
        )


def test_get_physical_assessment_raises_not_found():
    service, *_ = _make_service()

    with pytest.raises(PhysicalAssessmentNotFoundError):
        asyncio.run(
            service.get_physical_assessment(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                physical_assessment_id=uuid.uuid4(),
            )
        )


# --- get_client_physical_assessments (historical records) -----------------------------


def test_get_client_physical_assessments_preserves_full_history():
    service, physical_assessment_repository, client_repository, assignment_repository = _make_service()
    client, trainer, trainer_user_id = _setup_assigned_pair(
        client_repository, assignment_repository
    )
    now = datetime.now(timezone.utc)
    first = _make_physical_assessment(
        client.id, trainer.id, weight_kg=85, recorded_at=now - timedelta(days=30)
    )
    second = _make_physical_assessment(
        client.id, trainer.id, weight_kg=83, waist_cm=96, recorded_at=now - timedelta(days=15)
    )
    third = _make_physical_assessment(
        client.id,
        trainer.id,
        weight_kg=81,
        waist_cm=94,
        body_fat_percentage=18,
        recorded_at=now,
    )
    physical_assessment_repository.seed(first)
    physical_assessment_repository.seed(second)
    physical_assessment_repository.seed(third)

    history = asyncio.run(
        service.get_client_physical_assessments(
            actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), client_id=client.id
        )
    )

    assert len(history) == 3
    assert [m.weight_kg for m in history] == [81, 83, 85]


def test_get_client_physical_assessments_rejects_non_owning_client():
    service, _, client_repository, _ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    client_repository.seed(other_client, "other@example.com")

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_client_physical_assessments(
                actor_role=RoleName.CLIENT, actor_id=client_user_id, client_id=other_client.id
            )
        )


# --- get_latest_physical_assessment ----------------------------------------------------


def test_get_latest_physical_assessment_computes_change_from_previous():
    service, physical_assessment_repository, client_repository, assignment_repository = _make_service()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    now = datetime.now(timezone.utc)
    older = _make_physical_assessment(
        client.id, trainer.id, weight_kg=82, waist_cm=94, recorded_at=now - timedelta(days=14)
    )
    newest = _make_physical_assessment(
        client.id, trainer.id, weight_kg=80, waist_cm=92, recorded_at=now
    )
    physical_assessment_repository.seed(older)
    physical_assessment_repository.seed(newest)

    latest = asyncio.run(
        service.get_latest_physical_assessment(
            actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), client_id=client.id
        )
    )

    assert latest.weight_kg == 80
    assert latest.previous_weight_kg == 82
    assert latest.weight_change == -2
    assert latest.waist_cm == 92
    assert latest.previous_waist_cm == 94
    assert latest.waist_change == -2


def test_get_latest_physical_assessment_without_previous_returns_null_change():
    service, physical_assessment_repository, client_repository, assignment_repository = _make_service()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    physical_assessment_repository.seed(_make_physical_assessment(client.id, trainer.id, weight_kg=80))

    latest = asyncio.run(
        service.get_latest_physical_assessment(
            actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), client_id=client.id
        )
    )

    assert latest.weight_kg == 80
    assert latest.previous_weight_kg is None
    assert latest.weight_change is None


def test_get_latest_physical_assessment_raises_not_found_without_any_physical_assessments():
    service, _, client_repository, assignment_repository = _make_service()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)

    with pytest.raises(PhysicalAssessmentNotFoundError):
        asyncio.run(
            service.get_latest_physical_assessment(
                actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), client_id=client.id
            )
        )


def test_get_latest_physical_assessment_rejects_non_owning_client():
    service, physical_assessment_repository, client_repository, _ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    client_repository.seed(other_client, "other@example.com")
    physical_assessment_repository.seed(_make_physical_assessment(other_client.id, uuid.uuid4()))

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_latest_physical_assessment(
                actor_role=RoleName.CLIENT, actor_id=client_user_id, client_id=other_client.id
            )
        )


# --- update_physical_assessment ---------------------------------------------------------


def test_update_physical_assessment_succeeds_for_super_admin_within_edit_window():
    service, physical_assessment_repository, client_repository, assignment_repository = _make_service(
        edit_window_days=30
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    physical_assessment = _make_physical_assessment(client.id, trainer.id, weight_kg=80)
    physical_assessment_repository.seed(physical_assessment)

    detail = asyncio.run(
        service.update_physical_assessment(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            physical_assessment_id=physical_assessment.id,
            values={"weight_kg": 78},
        )
    )

    assert detail.weight_kg == 78
    assert detail.waist_cm == physical_assessment.waist_cm  # untouched fields preserved


def test_update_physical_assessment_succeeds_for_assigned_trainer():
    service, physical_assessment_repository, client_repository, assignment_repository = _make_service()
    client, trainer, trainer_user_id = _setup_assigned_pair(
        client_repository, assignment_repository
    )
    physical_assessment = _make_physical_assessment(client.id, trainer.id, weight_kg=80)
    physical_assessment_repository.seed(physical_assessment)

    detail = asyncio.run(
        service.update_physical_assessment(
            actor_role=RoleName.TRAINER,
            actor_id=trainer_user_id,
            physical_assessment_id=physical_assessment.id,
            values={"weight_kg": 79},
        )
    )

    assert detail.weight_kg == 79


def test_update_physical_assessment_rejects_unassigned_trainer():
    service, physical_assessment_repository, client_repository, assignment_repository = _make_service()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    physical_assessment = _make_physical_assessment(client.id, uuid.uuid4(), weight_kg=80)
    physical_assessment_repository.seed(physical_assessment)
    other_trainer_user_id = uuid.uuid4()
    assignment_repository.seed_trainer(_make_trainer(user_id=other_trainer_user_id))

    with pytest.raises(TrainerNotAssignedError):
        asyncio.run(
            service.update_physical_assessment(
                actor_role=RoleName.TRAINER,
                actor_id=other_trainer_user_id,
                physical_assessment_id=physical_assessment.id,
                values={"weight_kg": 79},
            )
        )


def test_update_physical_assessment_rejects_client_role():
    service, physical_assessment_repository, client_repository, assignment_repository = _make_service()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    physical_assessment = _make_physical_assessment(client.id, trainer.id, weight_kg=80)
    physical_assessment_repository.seed(physical_assessment)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.update_physical_assessment(
                actor_role=RoleName.CLIENT,
                actor_id=uuid.uuid4(),
                physical_assessment_id=physical_assessment.id,
                values={"weight_kg": 79},
            )
        )


def test_update_physical_assessment_raises_not_found():
    service, *_ = _make_service()

    with pytest.raises(PhysicalAssessmentNotFoundError):
        asyncio.run(
            service.update_physical_assessment(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                physical_assessment_id=uuid.uuid4(),
                values={"weight_kg": 79},
            )
        )


def test_update_physical_assessment_rejects_clearing_all_fields():
    service, physical_assessment_repository, client_repository, assignment_repository = _make_service()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    physical_assessment = _make_physical_assessment(
        client.id, trainer.id, weight_kg=80, body_fat_percentage=None, chest_cm=None,
        waist_cm=None, hips_cm=None, left_arm_cm=None, right_arm_cm=None,
        left_thigh_cm=None, right_thigh_cm=None, resting_heart_rate=None,
    )
    physical_assessment_repository.seed(physical_assessment)

    with pytest.raises(PhysicalAssessmentFieldsRequiredError):
        asyncio.run(
            service.update_physical_assessment(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                physical_assessment_id=physical_assessment.id,
                values={"weight_kg": None},
            )
        )


def test_update_physical_assessment_rejects_after_edit_window_expired():
    service, physical_assessment_repository, client_repository, assignment_repository = _make_service(
        edit_window_days=1
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    physical_assessment = _make_physical_assessment(
        client.id, trainer.id, weight_kg=80,
        recorded_at=datetime.now(timezone.utc) - timedelta(days=5),
    )
    physical_assessment_repository.seed(physical_assessment)

    with pytest.raises(PhysicalAssessmentEditWindowExpiredError):
        asyncio.run(
            service.update_physical_assessment(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                physical_assessment_id=physical_assessment.id,
                values={"weight_kg": 79},
            )
        )


# --- list_pending_physical_assessments ---------------------------------------------------


def test_list_pending_physical_assessments_returns_all_for_super_admin():
    service, physical_assessment_repository, client_repository, assignment_repository = _make_service(
        physical_assessment_overdue_days=14
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(other_client, "other@example.com")
    overdue_recorded_at = datetime.now(timezone.utc) - timedelta(days=20)
    physical_assessment_repository.seed_latest_row(
        LatestPhysicalAssessmentRow(
            client_id=client.id, client_name="Jane Doe", recorded_at=overdue_recorded_at
        )
    )
    physical_assessment_repository.seed_latest_row(
        LatestPhysicalAssessmentRow(
            client_id=other_client.id,
            client_name="Other Client",
            recorded_at=datetime.now(timezone.utc),
        )
    )

    result = asyncio.run(
        service.list_pending_physical_assessments(actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4())
    )

    assert len(result) == 1
    assert result[0].client_id == client.id
    assert result[0].days_overdue == 6


def test_list_pending_physical_assessments_scoped_to_assigned_clients_for_trainer():
    service, physical_assessment_repository, client_repository, assignment_repository = _make_service()
    client, trainer, trainer_user_id = _setup_assigned_pair(
        client_repository, assignment_repository
    )
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(other_client, "other@example.com")
    overdue_recorded_at = datetime.now(timezone.utc) - timedelta(days=20)
    physical_assessment_repository.seed_latest_row(
        LatestPhysicalAssessmentRow(
            client_id=client.id, client_name="Jane Doe", recorded_at=overdue_recorded_at
        )
    )
    physical_assessment_repository.seed_latest_row(
        LatestPhysicalAssessmentRow(
            client_id=other_client.id, client_name="Other Client", recorded_at=overdue_recorded_at
        )
    )

    result = asyncio.run(
        service.list_pending_physical_assessments(actor_role=RoleName.TRAINER, actor_id=trainer_user_id)
    )

    assert len(result) == 1
    assert result[0].client_id == client.id


def test_list_pending_physical_assessments_excludes_clients_within_window():
    service, physical_assessment_repository, client_repository, assignment_repository = _make_service(
        physical_assessment_overdue_days=14
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    physical_assessment_repository.seed_latest_row(
        LatestPhysicalAssessmentRow(
            client_id=client.id,
            client_name="Jane Doe",
            recorded_at=datetime.now(timezone.utc) - timedelta(days=5),
        )
    )

    result = asyncio.run(
        service.list_pending_physical_assessments(actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4())
    )

    assert result == []


def test_list_pending_physical_assessments_rejects_client_role():
    service, *_ = _make_service()

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.list_pending_physical_assessments(actor_role=RoleName.CLIENT, actor_id=uuid.uuid4())
        )
