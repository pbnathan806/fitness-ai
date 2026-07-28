import asyncio
import uuid
from datetime import datetime, time, timedelta, timezone

import pytest

from core.constants import RoleName
from models.role import Role
from models.trainer_availability import TrainerAvailability
from models.trainer_profile import TrainerProfile
from repositories.role_repository import RoleRepository
from repositories.trainer_availability_repository import TrainerAvailabilityRepository
from repositories.trainer_repository import TrainerRecord, TrainerRepository
from services.application_setting_service import ApplicationSettingService
from services.trainer_service import (
    AvailabilityNotFoundError,
    AvailabilityOverlapError,
    ForbiddenError,
    InvalidAvailabilityError,
    TrainerAlreadyExistsError,
    TrainerNotFoundError,
    TrainerService,
)
from tests.services.test_application_setting_service import (
    FakeApplicationSettingRepository,
    _make_setting,
)
from tests.services.test_assignment_service import FakeAssignmentRepository, _make_trainer
from tests.services.test_check_in_service import FakeCheckInRepository, _make_check_in
from tests.services.test_client_service import FakeClientRepository, FakeUserRepository
from tests.services.test_dashboard_service import FakeDashboardRepository
from tests.services.test_measurement_service import FakeMeasurementRepository
from tests.services.test_session_service import FakeSessionRepository, _make_session


class FakeRoleRepository(RoleRepository):
    def __init__(self) -> None:
        self._roles = {
            name: Role(id=uuid.uuid4(), name=name)
            for name in (RoleName.SUPER_ADMIN, RoleName.TRAINER, RoleName.CLIENT)
        }
        self._user_roles: dict[uuid.UUID, set[str]] = {}
        self.assignments: list[tuple[uuid.UUID, uuid.UUID]] = []

    def seed_role_for_user(self, user_id: uuid.UUID, role_name: str) -> None:
        self._user_roles.setdefault(user_id, set()).add(role_name)

    async def get_role_names_for_user(self, user_id: uuid.UUID) -> list[str]:
        return sorted(self._user_roles.get(user_id, set()))

    async def get_by_name(self, name: str) -> Role | None:
        return self._roles.get(name)

    async def assign_role_to_user(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        self.assignments.append((user_id, role_id))
        for name, role in self._roles.items():
            if role.id == role_id:
                self.seed_role_for_user(user_id, name)


class FakeTrainerRepository(TrainerRepository):
    def __init__(self) -> None:
        self._trainers: dict[uuid.UUID, TrainerProfile] = {}
        self._emails: dict[uuid.UUID, str] = {}

    def seed(self, trainer: TrainerProfile, email: str = "trainer@example.com") -> None:
        self._trainers[trainer.id] = trainer
        self._emails[trainer.id] = email

    async def create(self, trainer: TrainerProfile) -> TrainerProfile:
        now = datetime.now(timezone.utc)
        trainer.id = trainer.id or uuid.uuid4()
        trainer.created_at = now
        trainer.updated_at = now
        self._trainers[trainer.id] = trainer
        return trainer

    async def get_by_id(self, trainer_id: uuid.UUID) -> TrainerRecord | None:
        trainer = self._trainers.get(trainer_id)
        if trainer is None:
            return None
        return TrainerRecord(trainer=trainer, email=self._emails.get(trainer_id, ""))

    async def get_by_user_id(self, user_id: uuid.UUID) -> TrainerRecord | None:
        for trainer in self._trainers.values():
            if trainer.user_id == user_id:
                return TrainerRecord(trainer=trainer, email=self._emails.get(trainer.id, ""))
        return None

    async def update(self, trainer_id: uuid.UUID, values: dict) -> TrainerRecord | None:
        trainer = self._trainers.get(trainer_id)
        if trainer is None:
            return None
        for key, value in values.items():
            setattr(trainer, key, value)
        trainer.updated_at = datetime.now(timezone.utc)
        return TrainerRecord(trainer=trainer, email=self._emails.get(trainer_id, ""))

    async def list_paginated(
        self,
        offset: int,
        limit: int,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        is_active: bool | None = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> tuple[list[TrainerRecord], int]:
        matched = list(self._trainers.values())
        if first_name:
            matched = [t for t in matched if first_name.lower() in (t.first_name or "").lower()]
        if last_name:
            matched = [t for t in matched if last_name.lower() in (t.last_name or "").lower()]
        if email:
            matched = [
                t for t in matched if email.lower() in self._emails.get(t.id, "").lower()
            ]
        if is_active is not None:
            matched = [t for t in matched if bool(t.is_active) == is_active]

        key_fn = (lambda t: t.first_name or "") if sort_by == "first_name" else (lambda t: t.created_at)
        matched.sort(key=key_fn, reverse=sort_desc)

        total = len(matched)
        page = matched[offset : offset + limit]
        records = [
            TrainerRecord(trainer=t, email=self._emails.get(t.id, "")) for t in page
        ]
        return records, total


class FakeTrainerAvailabilityRepository(TrainerAvailabilityRepository):
    def __init__(self) -> None:
        self._slots: dict[uuid.UUID, TrainerAvailability] = {}

    async def create(self, availability: TrainerAvailability) -> TrainerAvailability:
        now = datetime.now(timezone.utc)
        availability.id = availability.id or uuid.uuid4()
        availability.created_at = now
        self._slots[availability.id] = availability
        return availability

    async def get_by_id(self, availability_id: uuid.UUID) -> TrainerAvailability | None:
        return self._slots.get(availability_id)

    async def list_for_trainer(self, trainer_id: uuid.UUID) -> list[TrainerAvailability]:
        matched = [s for s in self._slots.values() if s.trainer_id == trainer_id]
        return sorted(matched, key=lambda s: (s.weekday, s.start_time))

    async def update(
        self, availability_id: uuid.UUID, values: dict
    ) -> TrainerAvailability | None:
        slot = self._slots.get(availability_id)
        if slot is None:
            return None
        for key, value in values.items():
            setattr(slot, key, value)
        return slot

    async def delete(self, availability_id: uuid.UUID) -> bool:
        if availability_id in self._slots:
            del self._slots[availability_id]
            return True
        return False

    async def find_overlapping(
        self,
        trainer_id: uuid.UUID,
        weekday: int,
        start_time: time,
        end_time: time,
        exclude_id: uuid.UUID | None = None,
    ) -> TrainerAvailability | None:
        for slot in self._slots.values():
            if slot.trainer_id != trainer_id or slot.weekday != weekday:
                continue
            if exclude_id is not None and slot.id == exclude_id:
                continue
            if slot.start_time < end_time and slot.end_time > start_time:
                return slot
        return None


def _application_setting_service(measurement_overdue_days: int = 14) -> ApplicationSettingService:
    repository = FakeApplicationSettingRepository()
    repository.seed(
        _make_setting(key="measurement_overdue_days", value=str(measurement_overdue_days))
    )
    return ApplicationSettingService(repository)


def _make_service():
    trainer_repository = FakeTrainerRepository()
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    assignment_repository = FakeAssignmentRepository()
    session_repository = FakeSessionRepository()
    check_in_repository = FakeCheckInRepository()
    measurement_repository = FakeMeasurementRepository()
    trainer_availability_repository = FakeTrainerAvailabilityRepository()
    dashboard_repository = FakeDashboardRepository()
    application_setting_service = _application_setting_service()

    service = TrainerService(
        trainer_repository,
        user_repository,
        role_repository,
        assignment_repository,
        session_repository,
        check_in_repository,
        measurement_repository,
        trainer_availability_repository,
        dashboard_repository,
        application_setting_service,
    )
    return (
        service,
        trainer_repository,
        user_repository,
        role_repository,
        assignment_repository,
        session_repository,
        check_in_repository,
        measurement_repository,
        trainer_availability_repository,
    )


# ---------------------------------------------------------------------------
# CRUD / RBAC
# ---------------------------------------------------------------------------


def test_create_trainer_succeeds_for_super_admin():
    service, trainer_repository, user_repository, role_repository, *_ = _make_service()

    created = asyncio.run(
        service.create_trainer(
            actor_role=RoleName.SUPER_ADMIN,
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone_number="+15551234567",
            timezone="America/New_York",
        )
    )

    assert created.trainer.first_name == "Jane"
    assert created.trainer.email == "jane@example.com"
    assert created.trainer.is_active is True
    assert len(created.temporary_password) > 0
    assert user_repository.created[0].email == "jane@example.com"


def test_create_trainer_rejects_non_super_admin():
    service, *_ = _make_service()

    for role in (RoleName.TRAINER, RoleName.CLIENT, None):
        with pytest.raises(ForbiddenError):
            asyncio.run(
                service.create_trainer(
                    actor_role=role,
                    first_name="Jane",
                    last_name="Doe",
                    email="jane@example.com",
                    phone_number=None,
                    timezone="America/New_York",
                )
            )


def test_create_trainer_rejects_duplicate_email():
    service, trainer_repository, user_repository, *_ = _make_service()
    asyncio.run(
        service.create_trainer(
            actor_role=RoleName.SUPER_ADMIN,
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone_number=None,
            timezone="America/New_York",
        )
    )

    with pytest.raises(TrainerAlreadyExistsError):
        asyncio.run(
            service.create_trainer(
                actor_role=RoleName.SUPER_ADMIN,
                first_name="Jane",
                last_name="Doe2",
                email="jane@example.com",
                phone_number=None,
                timezone="America/New_York",
            )
        )


def test_get_trainer_succeeds_for_super_admin():
    service, trainer_repository, *_ = _make_service()
    trainer = _make_trainer(user_id=uuid.uuid4(), first_name="Jane", last_name="Doe", is_active=True)
    trainer_repository.seed(trainer)

    detail = asyncio.run(
        service.get_trainer(
            actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), trainer_id=trainer.id
        )
    )

    assert detail.id == trainer.id


def test_get_trainer_allows_self_only_for_trainer():
    service, trainer_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    other_trainer = _make_trainer(user_id=uuid.uuid4())
    trainer_repository.seed(trainer)
    trainer_repository.seed(other_trainer)

    detail = asyncio.run(
        service.get_trainer(
            actor_role=RoleName.TRAINER, actor_id=trainer_user_id, trainer_id=trainer.id
        )
    )
    assert detail.id == trainer.id

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_trainer(
                actor_role=RoleName.TRAINER, actor_id=trainer_user_id, trainer_id=other_trainer.id
            )
        )


def test_get_trainer_rejects_client():
    service, trainer_repository, *_ = _make_service()
    trainer = _make_trainer(user_id=uuid.uuid4())
    trainer_repository.seed(trainer)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_trainer(
                actor_role=RoleName.CLIENT, actor_id=uuid.uuid4(), trainer_id=trainer.id
            )
        )


def test_get_trainer_raises_not_found():
    service, *_ = _make_service()

    with pytest.raises(TrainerNotFoundError):
        asyncio.run(
            service.get_trainer(
                actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), trainer_id=uuid.uuid4()
            )
        )


def test_get_availability_succeeds_for_super_admin():
    (
        service,
        trainer_repository,
        *_,
        trainer_availability_repository,
    ) = _make_service()
    trainer = _make_trainer(user_id=uuid.uuid4())
    trainer_repository.seed(trainer)
    asyncio.run(
        trainer_availability_repository.create(
            TrainerAvailability(
                trainer_id=trainer.id,
                weekday=0,
                start_time=time(9, 0),
                end_time=time(10, 0),
                is_available=True,
            )
        )
    )

    slots = asyncio.run(
        service.get_availability(
            actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), trainer_id=trainer.id
        )
    )

    assert len(slots) == 1
    assert slots[0].trainer_id == trainer.id


def test_get_availability_allows_self_only_for_trainer():
    (
        service,
        trainer_repository,
        *_,
    ) = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    other_trainer = _make_trainer(user_id=uuid.uuid4())
    trainer_repository.seed(trainer)
    trainer_repository.seed(other_trainer)

    slots = asyncio.run(
        service.get_availability(
            actor_role=RoleName.TRAINER, actor_id=trainer_user_id, trainer_id=trainer.id
        )
    )
    assert slots == []

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_availability(
                actor_role=RoleName.TRAINER,
                actor_id=trainer_user_id,
                trainer_id=other_trainer.id,
            )
        )


def test_get_availability_rejects_client():
    service, trainer_repository, *_ = _make_service()
    trainer = _make_trainer(user_id=uuid.uuid4())
    trainer_repository.seed(trainer)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_availability(
                actor_role=RoleName.CLIENT, actor_id=uuid.uuid4(), trainer_id=trainer.id
            )
        )


def test_get_availability_raises_not_found():
    service, *_ = _make_service()

    with pytest.raises(TrainerNotFoundError):
        asyncio.run(
            service.get_availability(
                actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), trainer_id=uuid.uuid4()
            )
        )


def test_list_trainers_rejects_non_super_admin():
    service, *_ = _make_service()

    for role in (RoleName.TRAINER, RoleName.CLIENT, None):
        with pytest.raises(ForbiddenError):
            asyncio.run(service.list_trainers(actor_role=role, page=1, page_size=20))


def test_list_trainers_paginates_and_filters():
    service, trainer_repository, *_ = _make_service()
    now = datetime.now(timezone.utc)
    trainer_repository.seed(
        _make_trainer(
            user_id=uuid.uuid4(), first_name="Alice", last_name="Adams", created_at=now
        ),
        "alice@example.com",
    )
    trainer_repository.seed(
        _make_trainer(
            user_id=uuid.uuid4(),
            first_name="Bob",
            last_name="Brown",
            created_at=now + timedelta(seconds=1),
        ),
        "bob@example.com",
    )
    trainer_repository.seed(
        _make_trainer(
            user_id=uuid.uuid4(),
            first_name="Carol",
            last_name="Clark",
            created_at=now + timedelta(seconds=2),
        ),
        "carol@example.com",
    )

    result = asyncio.run(
        service.list_trainers(actor_role=RoleName.SUPER_ADMIN, page=1, page_size=2)
    )
    assert result.total == 3
    assert len(result.items) == 2

    filtered = asyncio.run(
        service.list_trainers(
            actor_role=RoleName.SUPER_ADMIN, page=1, page_size=20, first_name="Alice"
        )
    )
    assert filtered.total == 1
    assert filtered.items[0].first_name == "Alice"


def test_update_trainer_allows_super_admin_full_fields():
    service, trainer_repository, *_ = _make_service()
    trainer = _make_trainer(user_id=uuid.uuid4(), first_name="Jane", last_name="Doe")
    trainer_repository.seed(trainer)

    updated = asyncio.run(
        service.update_trainer(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            trainer_id=trainer.id,
            first_name="Janet",
            last_name=None,
            phone_number=None,
            timezone=None,
        )
    )

    assert updated.first_name == "Janet"


def test_update_trainer_restricts_trainer_to_phone_and_timezone():
    service, trainer_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id, first_name="Jane", last_name="Doe")
    trainer_repository.seed(trainer)

    updated = asyncio.run(
        service.update_trainer(
            actor_role=RoleName.TRAINER,
            actor_id=trainer_user_id,
            trainer_id=trainer.id,
            first_name=None,
            last_name=None,
            phone_number="+15559999999",
            timezone="America/Chicago",
        )
    )
    assert updated.phone_number == "+15559999999"
    assert updated.timezone == "America/Chicago"

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.update_trainer(
                actor_role=RoleName.TRAINER,
                actor_id=trainer_user_id,
                trainer_id=trainer.id,
                first_name="Someone Else",
                last_name=None,
                phone_number=None,
                timezone=None,
            )
        )


def test_update_trainer_rejects_trainer_editing_another_trainer():
    service, trainer_repository, *_ = _make_service()
    trainer = _make_trainer(user_id=uuid.uuid4())
    trainer_repository.seed(trainer)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.update_trainer(
                actor_role=RoleName.TRAINER,
                actor_id=uuid.uuid4(),
                trainer_id=trainer.id,
                first_name=None,
                last_name=None,
                phone_number="+15550000000",
                timezone=None,
            )
        )


def test_update_status_succeeds_for_super_admin():
    service, trainer_repository, _, role_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id, is_active=True)
    trainer_repository.seed(trainer)
    role_repository.seed_role_for_user(trainer_user_id, RoleName.TRAINER)

    updated = asyncio.run(
        service.update_status(
            actor_role=RoleName.SUPER_ADMIN, trainer_id=trainer.id, is_active=False
        )
    )

    assert updated.is_active is False


def test_update_status_rejects_non_super_admin():
    service, trainer_repository, *_ = _make_service()
    trainer = _make_trainer(user_id=uuid.uuid4())
    trainer_repository.seed(trainer)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.update_status(
                actor_role=RoleName.TRAINER, trainer_id=trainer.id, is_active=False
            )
        )


def test_update_status_cannot_deactivate_super_admin():
    service, trainer_repository, _, role_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id, is_active=True)
    trainer_repository.seed(trainer)
    role_repository.seed_role_for_user(trainer_user_id, RoleName.SUPER_ADMIN)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.update_status(
                actor_role=RoleName.SUPER_ADMIN, trainer_id=trainer.id, is_active=False
            )
        )


# ---------------------------------------------------------------------------
# Self profile
# ---------------------------------------------------------------------------


def test_get_self_succeeds_for_trainer():
    service, trainer_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    trainer_repository.seed(trainer)

    detail = asyncio.run(service.get_self(actor_role=RoleName.TRAINER, actor_id=trainer_user_id))
    assert detail.id == trainer.id


def test_get_self_rejects_non_trainer():
    service, *_ = _make_service()

    for role in (RoleName.SUPER_ADMIN, RoleName.CLIENT, None):
        with pytest.raises(ForbiddenError):
            asyncio.run(service.get_self(actor_role=role, actor_id=uuid.uuid4()))


def test_update_self_only_allows_phone_and_timezone():
    service, trainer_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    trainer_repository.seed(trainer)

    updated = asyncio.run(
        service.update_self(
            actor_role=RoleName.TRAINER,
            actor_id=trainer_user_id,
            phone_number="+15551112222",
            timezone="Asia/Kolkata",
        )
    )

    assert updated.phone_number == "+15551112222"
    assert updated.timezone == "Asia/Kolkata"


# ---------------------------------------------------------------------------
# Summary / performance
# ---------------------------------------------------------------------------


def test_get_summary_returns_zero_metrics_with_no_data():
    service, trainer_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    trainer_repository.seed(trainer)

    summary = asyncio.run(
        service.get_summary(
            actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), trainer_id=trainer.id
        )
    )

    assert summary.assigned_clients == 0
    assert summary.sessions_this_week == 0
    assert summary.completed_sessions_this_month == 0
    assert summary.pending_check_ins == 0
    assert summary.pending_measurements == 0


def test_get_performance_returns_zero_metrics_with_no_data():
    service, trainer_repository, *_ = _make_service()
    trainer = _make_trainer(user_id=uuid.uuid4())
    trainer_repository.seed(trainer)

    performance = asyncio.run(
        service.get_performance(
            actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), trainer_id=trainer.id
        )
    )

    assert performance.assigned_clients == 0
    assert performance.completed_sessions == 0
    assert performance.completion_rate == 0
    assert performance.average_check_in_rate == 0


def test_get_performance_computes_completion_rate():
    (
        service,
        trainer_repository,
        _,
        _role_repository,
        assignment_repository,
        session_repository,
        *_rest,
    ) = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    trainer_repository.seed(trainer)

    from models.session import SessionStatus

    client_id = uuid.uuid4()
    session_repository.seed(
        _make_session(client_id=client_id, trainer_id=trainer.id, status=SessionStatus.COMPLETED)
    )
    session_repository.seed(
        _make_session(client_id=client_id, trainer_id=trainer.id, status=SessionStatus.CANCELLED)
    )

    performance = asyncio.run(
        service.get_performance(
            actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), trainer_id=trainer.id
        )
    )

    assert performance.completed_sessions == 1
    assert performance.completion_rate == 50


def test_get_summary_rejects_trainer_for_another_trainer():
    service, trainer_repository, *_ = _make_service()
    trainer = _make_trainer(user_id=uuid.uuid4())
    trainer_repository.seed(trainer)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_summary(
                actor_role=RoleName.TRAINER, actor_id=uuid.uuid4(), trainer_id=trainer.id
            )
        )


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------


def test_create_availability_succeeds_for_trainer():
    service, trainer_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    trainer_repository.seed(trainer)

    detail = asyncio.run(
        service.create_availability(
            actor_role=RoleName.TRAINER,
            actor_id=trainer_user_id,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(10, 0),
            is_available=True,
        )
    )

    assert detail.trainer_id == trainer.id
    assert detail.weekday == 0


def test_create_availability_rejects_non_trainer():
    service, *_ = _make_service()

    for role in (RoleName.SUPER_ADMIN, RoleName.CLIENT, None):
        with pytest.raises(ForbiddenError):
            asyncio.run(
                service.create_availability(
                    actor_role=role,
                    actor_id=uuid.uuid4(),
                    weekday=0,
                    start_time=time(9, 0),
                    end_time=time(10, 0),
                    is_available=True,
                )
            )


def test_create_availability_rejects_invalid_time_range():
    service, trainer_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer_repository.seed(_make_trainer(user_id=trainer_user_id))

    with pytest.raises(InvalidAvailabilityError):
        asyncio.run(
            service.create_availability(
                actor_role=RoleName.TRAINER,
                actor_id=trainer_user_id,
                weekday=0,
                start_time=time(10, 0),
                end_time=time(9, 0),
                is_available=True,
            )
        )


def test_create_availability_rejects_overlap():
    service, trainer_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer_repository.seed(_make_trainer(user_id=trainer_user_id))

    asyncio.run(
        service.create_availability(
            actor_role=RoleName.TRAINER,
            actor_id=trainer_user_id,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(11, 0),
            is_available=True,
        )
    )

    with pytest.raises(AvailabilityOverlapError):
        asyncio.run(
            service.create_availability(
                actor_role=RoleName.TRAINER,
                actor_id=trainer_user_id,
                weekday=0,
                start_time=time(10, 0),
                end_time=time(12, 0),
                is_available=True,
            )
        )


def test_update_availability_allows_non_overlapping_change():
    service, trainer_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer_repository.seed(_make_trainer(user_id=trainer_user_id))

    created = asyncio.run(
        service.create_availability(
            actor_role=RoleName.TRAINER,
            actor_id=trainer_user_id,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(11, 0),
            is_available=True,
        )
    )

    updated = asyncio.run(
        service.update_availability(
            actor_role=RoleName.TRAINER,
            actor_id=trainer_user_id,
            availability_id=created.id,
            weekday=1,
            start_time=time(9, 0),
            end_time=time(11, 0),
            is_available=False,
        )
    )

    assert updated.weekday == 1
    assert updated.is_available is False


def test_delete_availability_succeeds_for_owning_trainer():
    service, trainer_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer_repository.seed(_make_trainer(user_id=trainer_user_id))

    created = asyncio.run(
        service.create_availability(
            actor_role=RoleName.TRAINER,
            actor_id=trainer_user_id,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(11, 0),
            is_available=True,
        )
    )

    asyncio.run(
        service.delete_availability(
            actor_role=RoleName.TRAINER, actor_id=trainer_user_id, availability_id=created.id
        )
    )

    with pytest.raises(AvailabilityNotFoundError):
        asyncio.run(
            service.update_availability(
                actor_role=RoleName.TRAINER,
                actor_id=trainer_user_id,
                availability_id=created.id,
                weekday=0,
                start_time=time(9, 0),
                end_time=time(11, 0),
                is_available=True,
            )
        )


def test_delete_availability_rejects_other_trainer():
    service, trainer_repository, *_ = _make_service()
    owner_user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    trainer_repository.seed(_make_trainer(user_id=owner_user_id))
    trainer_repository.seed(_make_trainer(user_id=other_user_id))

    created = asyncio.run(
        service.create_availability(
            actor_role=RoleName.TRAINER,
            actor_id=owner_user_id,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(11, 0),
            is_available=True,
        )
    )

    with pytest.raises(AvailabilityNotFoundError):
        asyncio.run(
            service.delete_availability(
                actor_role=RoleName.TRAINER,
                actor_id=other_user_id,
                availability_id=created.id,
            )
        )
