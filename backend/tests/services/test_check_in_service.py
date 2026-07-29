import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from core.constants import RoleName
from models.application_setting import ApplicationSetting
from models.check_in import CheckIn
from models.client_trainer_assignment import ClientTrainerAssignment
from models.session import SessionStatus
from repositories.check_in_repository import CheckInRepository, PendingCheckInRow
from services.application_setting_service import ApplicationSettingService
from services.check_in_service import (
    CheckInEditWindowExpiredError,
    CheckInFieldsRequiredError,
    CheckInNotFoundError,
    CheckInService,
    ClientNotFoundError,
    DuplicateCheckInError,
    ForbiddenError,
    SessionCancelledError,
    SessionNotFoundError,
    SessionNotStartedError,
    TrainerNotAssignedError,
    TrainerNotFoundError,
)
from tests.services.test_application_setting_service import FakeApplicationSettingRepository
from tests.services.test_assignment_service import FakeAssignmentRepository, _make_trainer
from tests.services.test_client_service import FakeClientRepository, _make_client
from tests.services.test_session_service import FakeSessionRepository, _make_session


class FakeCheckInRepository(CheckInRepository):
    def __init__(self) -> None:
        self._check_ins: dict[uuid.UUID, CheckIn] = {}
        self._pending_rows: list[PendingCheckInRow] = []

    def seed(self, check_in: CheckIn) -> None:
        self._check_ins[check_in.id] = check_in

    def seed_pending_row(self, row: PendingCheckInRow) -> None:
        self._pending_rows.append(row)

    async def create(self, check_in: CheckIn) -> CheckIn:
        now = datetime.now(timezone.utc)
        check_in.id = check_in.id or uuid.uuid4()
        check_in.created_at = now
        check_in.updated_at = now
        self._check_ins[check_in.id] = check_in
        return check_in

    async def update(self, check_in: CheckIn) -> CheckIn:
        check_in.updated_at = datetime.now(timezone.utc)
        self._check_ins[check_in.id] = check_in
        return check_in

    async def get_by_id(self, check_in_id: uuid.UUID) -> CheckIn | None:
        return self._check_ins.get(check_in_id)

    async def get_by_session_id(self, session_id: uuid.UUID) -> CheckIn | None:
        for check_in in self._check_ins.values():
            if check_in.session_id == session_id:
                return check_in
        return None

    async def list_paginated(self, offset: int, limit: int) -> tuple[list[CheckIn], int]:
        ordered = sorted(
            self._check_ins.values(), key=lambda c: c.submitted_at, reverse=True
        )
        return ordered[offset : offset + limit], len(ordered)

    async def list_for_client(
        self, client_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[CheckIn], int]:
        matched = [c for c in self._check_ins.values() if c.client_id == client_id]
        ordered = sorted(matched, key=lambda c: c.submitted_at, reverse=True)
        return ordered[offset : offset + limit], len(ordered)

    async def list_for_clients(
        self, client_ids: list[uuid.UUID], offset: int, limit: int
    ) -> tuple[list[CheckIn], int]:
        matched = [c for c in self._check_ins.values() if c.client_id in client_ids]
        ordered = sorted(matched, key=lambda c: c.submitted_at, reverse=True)
        return ordered[offset : offset + limit], len(ordered)

    async def list_all_for_client(self, client_id: uuid.UUID) -> list[CheckIn]:
        matched = [c for c in self._check_ins.values() if c.client_id == client_id]
        return sorted(matched, key=lambda c: c.submitted_at, reverse=True)

    async def count_in_range(
        self, start: datetime, end: datetime, client_ids: list[uuid.UUID] | None = None
    ) -> int:
        return sum(
            1
            for c in self._check_ins.values()
            if start <= c.submitted_at < end
            and (client_ids is None or c.client_id in client_ids)
        )

    async def list_pending(
        self, client_ids: list[uuid.UUID] | None, now: datetime
    ) -> list[PendingCheckInRow]:
        if client_ids is None:
            return list(self._pending_rows)
        return [row for row in self._pending_rows if row.client_id in client_ids]

    async def count_pending(self, client_ids: list[uuid.UUID] | None, now: datetime) -> int:
        return len(await self.list_pending(client_ids, now))

    async def count_for_client(self, client_id: uuid.UUID) -> int:
        return sum(1 for c in self._check_ins.values() if c.client_id == client_id)


def _make_check_in(session_id: uuid.UUID, client_id: uuid.UUID, submitted_by: uuid.UUID, **overrides) -> CheckIn:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid.uuid4(),
        session_id=session_id,
        client_id=client_id,
        sleep_hours=7.5,
        water_intake_liters=3,
        energy_level=4,
        mood=5,
        workout_completed=True,
        diet_followed=True,
        notes=None,
        submitted_by=submitted_by,
        submitted_at=now,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return CheckIn(**defaults)


def _make_application_setting_service(edit_window_days: int = 30) -> ApplicationSettingService:
    repository = FakeApplicationSettingRepository()
    repository.seed(
        ApplicationSetting(
            id=uuid.uuid4(),
            key="check_in_edit_window_days",
            value=str(edit_window_days),
            description="Edit window",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )
    return ApplicationSettingService(repository)


def _make_service(edit_window_days: int = 30) -> tuple[
    CheckInService,
    FakeCheckInRepository,
    FakeClientRepository,
    FakeAssignmentRepository,
    FakeSessionRepository,
]:
    check_in_repository = FakeCheckInRepository()
    client_repository = FakeClientRepository()
    assignment_repository = FakeAssignmentRepository()
    session_repository = FakeSessionRepository()
    application_setting_service = _make_application_setting_service(edit_window_days)
    service = CheckInService(
        check_in_repository,
        client_repository,
        assignment_repository,
        session_repository,
        application_setting_service,
    )
    return service, check_in_repository, client_repository, assignment_repository, session_repository


def _setup_assigned_pair(client_repository, assignment_repository, client_timezone="UTC"):
    client = _make_client(user_id=uuid.uuid4(), timezone=client_timezone)
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


def _create_kwargs(session_id: uuid.UUID, **overrides) -> dict:
    defaults = dict(
        session_id=session_id,
        sleep_hours=None,
        water_intake_liters=None,
        energy_level=None,
        mood=None,
        workout_completed=None,
        diet_followed=None,
        notes=None,
    )
    defaults.update(overrides)
    return defaults


def _past_session(session_repository, client_id, trainer_id, **overrides):
    started = datetime.now(timezone.utc) - timedelta(days=2)
    session = _make_session(
        client_id, trainer_id, scheduled_start=started, scheduled_end=started + timedelta(hours=1), **overrides
    )
    session_repository.seed(session)
    return session


# --- create_check_in ----------------------------------------------------------


def test_create_check_in_succeeds_for_super_admin():
    service, _, client_repository, assignment_repository, session_repository = _make_service()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id)

    detail = asyncio.run(
        service.create_check_in(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            **_create_kwargs(session.id, sleep_hours=7.5, mood=5),
        )
    )

    assert detail.session_id == session.id
    assert detail.client_id == client.id
    assert detail.sleep_hours == 7.5
    assert detail.mood == 5


def test_create_check_in_succeeds_for_assigned_trainer():
    service, _, client_repository, assignment_repository, session_repository = _make_service()
    client, trainer, trainer_user_id = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id)

    detail = asyncio.run(
        service.create_check_in(
            actor_role=RoleName.TRAINER,
            actor_id=trainer_user_id,
            **_create_kwargs(session.id, energy_level=4),
        )
    )

    assert detail.client_id == client.id
    assert detail.submitted_by == trainer_user_id


def test_create_check_in_succeeds_for_own_client():
    service, _, client_repository, assignment_repository, session_repository = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    client_repository.seed(client, "client@example.com")
    session = _past_session(session_repository, client.id, uuid.uuid4())

    detail = asyncio.run(
        service.create_check_in(
            actor_role=RoleName.CLIENT,
            actor_id=client_user_id,
            **_create_kwargs(session.id, mood=4, workout_completed=True),
        )
    )

    assert detail.client_id == client.id
    assert detail.submitted_by == client_user_id
    assert detail.mood == 4


def test_create_check_in_rejects_unassigned_trainer():
    service, _, client_repository, assignment_repository, session_repository = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    session = _past_session(session_repository, client.id, uuid.uuid4())
    # Note: no assignment created between trainer and client.

    with pytest.raises(TrainerNotAssignedError):
        asyncio.run(
            service.create_check_in(
                actor_role=RoleName.TRAINER,
                actor_id=trainer_user_id,
                **_create_kwargs(session.id, mood=3),
            )
        )


def test_create_check_in_rejects_client_submitting_for_another_clients_session():
    service, _, client_repository, assignment_repository, session_repository = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    client_repository.seed(other_client, "other@example.com")
    session = _past_session(session_repository, other_client.id, uuid.uuid4())

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.create_check_in(
                actor_role=RoleName.CLIENT,
                actor_id=client_user_id,
                **_create_kwargs(session.id, mood=4),
            )
        )


def test_create_check_in_rejects_empty_payload():
    service, _, client_repository, assignment_repository, session_repository = _make_service()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id)

    with pytest.raises(CheckInFieldsRequiredError):
        asyncio.run(
            service.create_check_in(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                **_create_kwargs(session.id),
            )
        )


def test_create_check_in_raises_when_session_missing():
    service, *_ = _make_service()

    with pytest.raises(SessionNotFoundError):
        asyncio.run(
            service.create_check_in(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                **_create_kwargs(uuid.uuid4(), mood=3),
            )
        )


def test_create_check_in_raises_when_trainer_profile_missing():
    service, _, client_repository, assignment_repository, session_repository = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    session = _past_session(session_repository, client.id, uuid.uuid4())

    with pytest.raises(TrainerNotFoundError):
        asyncio.run(
            service.create_check_in(
                actor_role=RoleName.TRAINER,
                actor_id=uuid.uuid4(),
                **_create_kwargs(session.id, mood=3),
            )
        )


def test_create_check_in_rejects_cancelled_session():
    service, _, client_repository, assignment_repository, session_repository = _make_service()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id, status=SessionStatus.CANCELLED)

    with pytest.raises(SessionCancelledError):
        asyncio.run(
            service.create_check_in(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                **_create_kwargs(session.id, mood=3),
            )
        )


def test_create_check_in_rejects_session_not_yet_started():
    service, _, client_repository, assignment_repository, session_repository = _make_service()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    future_start = datetime.now(timezone.utc) + timedelta(days=1)
    session = _make_session(
        client.id, trainer.id, scheduled_start=future_start, scheduled_end=future_start + timedelta(hours=1)
    )
    session_repository.seed(session)

    with pytest.raises(SessionNotStartedError):
        asyncio.run(
            service.create_check_in(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                **_create_kwargs(session.id, mood=3),
            )
        )


def test_create_check_in_prevents_duplicate_for_session():
    service, _, client_repository, assignment_repository, session_repository = _make_service()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id)

    asyncio.run(
        service.create_check_in(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            **_create_kwargs(session.id, mood=3),
        )
    )

    with pytest.raises(DuplicateCheckInError):
        asyncio.run(
            service.create_check_in(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                **_create_kwargs(session.id, mood=5),
            )
        )


def test_create_check_in_allows_second_session_for_same_client():
    service, _, client_repository, assignment_repository, session_repository = _make_service()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    session_one = _past_session(session_repository, client.id, trainer.id)
    session_two = _past_session(session_repository, client.id, trainer.id)

    asyncio.run(
        service.create_check_in(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            **_create_kwargs(session_one.id, mood=3),
        )
    )

    detail = asyncio.run(
        service.create_check_in(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            **_create_kwargs(session_two.id, mood=5),
        )
    )

    assert detail.mood == 5


# --- update_check_in -----------------------------------------------------------


def test_update_check_in_succeeds_within_edit_window():
    service, check_in_repository, client_repository, assignment_repository, session_repository = _make_service(
        edit_window_days=30
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id)
    check_in = _make_check_in(session.id, client.id, trainer.id, mood=3)
    check_in_repository.seed(check_in)

    detail = asyncio.run(
        service.update_check_in(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            check_in_id=check_in.id,
            values={"mood": 5},
        )
    )

    assert detail.mood == 5
    assert detail.sleep_hours == check_in.sleep_hours  # untouched fields preserved


def test_update_check_in_rejects_after_edit_window_expired():
    service, check_in_repository, client_repository, assignment_repository, session_repository = _make_service(
        edit_window_days=1
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    started = datetime.now(timezone.utc) - timedelta(days=5)
    session = _make_session(
        client.id, trainer.id, scheduled_start=started, scheduled_end=started + timedelta(hours=1)
    )
    session_repository.seed(session)
    check_in = _make_check_in(session.id, client.id, trainer.id, mood=3)
    check_in_repository.seed(check_in)

    with pytest.raises(CheckInEditWindowExpiredError):
        asyncio.run(
            service.update_check_in(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                check_in_id=check_in.id,
                values={"mood": 5},
            )
        )


def test_update_check_in_rejects_forbidden_actor():
    service, check_in_repository, client_repository, assignment_repository, session_repository = _make_service()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    other_client_user_id = uuid.uuid4()
    other_client = _make_client(user_id=other_client_user_id)
    client_repository.seed(other_client, "other@example.com")
    session = _past_session(session_repository, client.id, trainer.id)
    check_in = _make_check_in(session.id, client.id, trainer.id, mood=3)
    check_in_repository.seed(check_in)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.update_check_in(
                actor_role=RoleName.CLIENT,
                actor_id=other_client_user_id,
                check_in_id=check_in.id,
                values={"mood": 5},
            )
        )


def test_update_check_in_raises_not_found():
    service, *_ = _make_service()

    with pytest.raises(CheckInNotFoundError):
        asyncio.run(
            service.update_check_in(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                check_in_id=uuid.uuid4(),
                values={"mood": 5},
            )
        )


def test_update_check_in_rejects_clearing_all_fields():
    service, check_in_repository, client_repository, assignment_repository, session_repository = _make_service()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id)
    check_in = _make_check_in(
        session.id,
        client.id,
        trainer.id,
        sleep_hours=7.5,
        water_intake_liters=3,
        energy_level=4,
        mood=5,
        workout_completed=True,
        diet_followed=True,
        notes=None,
    )
    check_in_repository.seed(check_in)

    with pytest.raises(CheckInFieldsRequiredError):
        asyncio.run(
            service.update_check_in(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                check_in_id=check_in.id,
                values={
                    "sleep_hours": None,
                    "water_intake_liters": None,
                    "energy_level": None,
                    "mood": None,
                    "workout_completed": None,
                    "diet_followed": None,
                },
            )
        )


# --- list_check_ins -------------------------------------------------------------


def test_list_check_ins_returns_all_for_super_admin():
    service, check_in_repository, *_ = _make_service()
    for _ in range(3):
        check_in_repository.seed(_make_check_in(uuid.uuid4(), uuid.uuid4(), uuid.uuid4()))

    result = asyncio.run(
        service.list_check_ins(
            actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), page=1, page_size=2
        )
    )

    assert result.total == 3
    assert len(result.items) == 2


def test_list_check_ins_returns_only_assigned_clients_for_trainer():
    service, check_in_repository, client_repository, assignment_repository, _ = _make_service()
    client, trainer, trainer_user_id = _setup_assigned_pair(client_repository, assignment_repository)
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(other_client, "other@example.com")
    check_in_repository.seed(_make_check_in(uuid.uuid4(), client.id, trainer.id))
    check_in_repository.seed(_make_check_in(uuid.uuid4(), other_client.id, uuid.uuid4()))

    result = asyncio.run(
        service.list_check_ins(
            actor_role=RoleName.TRAINER, actor_id=trainer_user_id, page=1, page_size=20
        )
    )

    assert result.total == 1
    assert result.items[0].client_id == client.id


def test_list_check_ins_returns_only_own_for_client():
    service, check_in_repository, client_repository, _, _ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    check_in_repository.seed(_make_check_in(uuid.uuid4(), client.id, uuid.uuid4()))
    check_in_repository.seed(_make_check_in(uuid.uuid4(), other_client.id, uuid.uuid4()))

    result = asyncio.run(
        service.list_check_ins(
            actor_role=RoleName.CLIENT, actor_id=client_user_id, page=1, page_size=20
        )
    )

    assert result.total == 1
    assert result.items[0].client_id == client.id


# --- get_check_in / get_check_in_by_session -------------------------------------


def test_get_check_in_succeeds_for_owning_client():
    service, check_in_repository, client_repository, _, _ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    client_repository.seed(client, "client@example.com")
    check_in = _make_check_in(uuid.uuid4(), client.id, uuid.uuid4())
    check_in_repository.seed(check_in)

    detail = asyncio.run(
        service.get_check_in(
            actor_role=RoleName.CLIENT, actor_id=client_user_id, check_in_id=check_in.id
        )
    )

    assert detail.id == check_in.id


def test_get_check_in_rejects_non_owning_client():
    service, check_in_repository, client_repository, _, _ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    client_repository.seed(client, "client@example.com")
    check_in = _make_check_in(uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
    check_in_repository.seed(check_in)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_check_in(
                actor_role=RoleName.CLIENT, actor_id=client_user_id, check_in_id=check_in.id
            )
        )


def test_get_check_in_raises_not_found():
    service, *_ = _make_service()

    with pytest.raises(CheckInNotFoundError):
        asyncio.run(
            service.get_check_in(
                actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), check_in_id=uuid.uuid4()
            )
        )


def test_get_check_in_by_session_returns_detail():
    service, check_in_repository, client_repository, assignment_repository, session_repository = _make_service()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id)
    check_in = _make_check_in(session.id, client.id, trainer.id, mood=4)
    check_in_repository.seed(check_in)

    detail = asyncio.run(
        service.get_check_in_by_session(
            actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), session_id=session.id
        )
    )

    assert detail.id == check_in.id
    assert detail.mood == 4


def test_get_check_in_by_session_raises_not_found_without_check_in():
    service, _, client_repository, assignment_repository, session_repository = _make_service()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id)

    with pytest.raises(CheckInNotFoundError):
        asyncio.run(
            service.get_check_in_by_session(
                actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), session_id=session.id
            )
        )


def test_get_check_in_by_session_raises_session_not_found():
    service, *_ = _make_service()

    with pytest.raises(SessionNotFoundError):
        asyncio.run(
            service.get_check_in_by_session(
                actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), session_id=uuid.uuid4()
            )
        )


# --- get_client_check_ins (historical records) ----------------------------------


def test_get_client_check_ins_preserves_full_history():
    service, check_in_repository, client_repository, assignment_repository, _ = _make_service()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    now = datetime.now(timezone.utc)
    first = _make_check_in(uuid.uuid4(), client.id, trainer.id, mood=3, submitted_at=now - timedelta(days=2))
    second = _make_check_in(uuid.uuid4(), client.id, trainer.id, mood=4, submitted_at=now - timedelta(days=1))
    third = _make_check_in(uuid.uuid4(), client.id, trainer.id, mood=5, submitted_at=now)
    check_in_repository.seed(first)
    check_in_repository.seed(second)
    check_in_repository.seed(third)

    history = asyncio.run(
        service.get_client_check_ins(
            actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), client_id=client.id
        )
    )

    assert len(history) == 3
    assert [c.mood for c in history] == [5, 4, 3]


def test_get_client_check_ins_rejects_non_owning_client():
    service, _, client_repository, _, _ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    client_repository.seed(other_client, "other@example.com")

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_client_check_ins(
                actor_role=RoleName.CLIENT, actor_id=client_user_id, client_id=other_client.id
            )
        )


# --- list_pending_check_ins -----------------------------------------------------


def test_list_pending_check_ins_returns_all_for_super_admin():
    service, check_in_repository, client_repository, assignment_repository, _ = _make_service()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(other_client, "other@example.com")
    scheduled_start = datetime.now(timezone.utc) - timedelta(days=2)
    check_in_repository.seed_pending_row(
        PendingCheckInRow(
            session_id=uuid.uuid4(),
            client_id=client.id,
            client_name="Jane Doe",
            scheduled_start=scheduled_start,
        )
    )
    check_in_repository.seed_pending_row(
        PendingCheckInRow(
            session_id=uuid.uuid4(),
            client_id=other_client.id,
            client_name="Other Client",
            scheduled_start=scheduled_start,
        )
    )

    result = asyncio.run(
        service.list_pending_check_ins(actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4())
    )

    assert len(result) == 2
    assert result[0].days_pending == 2


def test_list_pending_check_ins_scoped_to_assigned_clients_for_trainer():
    service, check_in_repository, client_repository, assignment_repository, _ = _make_service()
    client, trainer, trainer_user_id = _setup_assigned_pair(client_repository, assignment_repository)
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(other_client, "other@example.com")
    scheduled_start = datetime.now(timezone.utc) - timedelta(days=1)
    check_in_repository.seed_pending_row(
        PendingCheckInRow(
            session_id=uuid.uuid4(),
            client_id=client.id,
            client_name="Jane Doe",
            scheduled_start=scheduled_start,
        )
    )
    check_in_repository.seed_pending_row(
        PendingCheckInRow(
            session_id=uuid.uuid4(),
            client_id=other_client.id,
            client_name="Other Client",
            scheduled_start=scheduled_start,
        )
    )

    result = asyncio.run(
        service.list_pending_check_ins(actor_role=RoleName.TRAINER, actor_id=trainer_user_id)
    )

    assert len(result) == 1
    assert result[0].client_id == client.id


def test_list_pending_check_ins_rejects_client_role():
    service, *_ = _make_service()

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.list_pending_check_ins(actor_role=RoleName.CLIENT, actor_id=uuid.uuid4())
        )
