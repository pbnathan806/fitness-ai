import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from core.constants import RoleName
from models.check_in import CheckIn
from models.client_trainer_assignment import ClientTrainerAssignment
from repositories.check_in_repository import CheckInRepository
from services.check_in_service import (
    CheckInFieldsRequiredError,
    CheckInNotFoundError,
    CheckInService,
    ClientNotFoundError,
    DuplicateCheckInError,
    ForbiddenError,
    TrainerNotAssignedError,
    TrainerNotFoundError,
)
from tests.services.test_assignment_service import FakeAssignmentRepository, _make_trainer
from tests.services.test_client_service import FakeClientRepository, _make_client


class FakeCheckInRepository(CheckInRepository):
    def __init__(self) -> None:
        self._check_ins: dict[uuid.UUID, CheckIn] = {}

    def seed(self, check_in: CheckIn) -> None:
        self._check_ins[check_in.id] = check_in

    async def create(self, check_in: CheckIn) -> CheckIn:
        now = datetime.now(timezone.utc)
        check_in.id = check_in.id or uuid.uuid4()
        check_in.created_at = now
        check_in.updated_at = now
        self._check_ins[check_in.id] = check_in
        return check_in

    async def get_by_id(self, check_in_id: uuid.UUID) -> CheckIn | None:
        return self._check_ins.get(check_in_id)

    async def get_for_client_in_range(
        self, client_id: uuid.UUID, start: datetime, end: datetime
    ) -> CheckIn | None:
        for check_in in self._check_ins.values():
            if check_in.client_id == client_id and start <= check_in.submitted_at < end:
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


def _make_check_in(client_id: uuid.UUID, submitted_by: uuid.UUID, **overrides) -> CheckIn:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid.uuid4(),
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


def _make_service() -> tuple[
    CheckInService, FakeCheckInRepository, FakeClientRepository, FakeAssignmentRepository
]:
    check_in_repository = FakeCheckInRepository()
    client_repository = FakeClientRepository()
    assignment_repository = FakeAssignmentRepository()
    service = CheckInService(check_in_repository, client_repository, assignment_repository)
    return service, check_in_repository, client_repository, assignment_repository


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


def _create_kwargs(client_id: uuid.UUID, **overrides) -> dict:
    defaults = dict(
        client_id=client_id,
        submitted_at=None,
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


# --- create_check_in ----------------------------------------------------------


def test_create_check_in_succeeds_for_super_admin():
    service, _, client_repository, assignment_repository = _make_service()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)

    detail = asyncio.run(
        service.create_check_in(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            **_create_kwargs(client.id, sleep_hours=7.5, mood=5),
        )
    )

    assert detail.client_id == client.id
    assert detail.sleep_hours == 7.5
    assert detail.mood == 5


def test_create_check_in_succeeds_for_assigned_trainer():
    service, _, client_repository, assignment_repository = _make_service()
    client, trainer, trainer_user_id = _setup_assigned_pair(
        client_repository, assignment_repository
    )

    detail = asyncio.run(
        service.create_check_in(
            actor_role=RoleName.TRAINER,
            actor_id=trainer_user_id,
            **_create_kwargs(client.id, energy_level=4),
        )
    )

    assert detail.client_id == client.id
    assert detail.submitted_by == trainer_user_id


def test_create_check_in_rejects_unassigned_trainer():
    service, _, client_repository, assignment_repository = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    # Note: no assignment created between trainer and client.

    with pytest.raises(TrainerNotAssignedError):
        asyncio.run(
            service.create_check_in(
                actor_role=RoleName.TRAINER,
                actor_id=trainer_user_id,
                **_create_kwargs(client.id, mood=3),
            )
        )


def test_create_check_in_succeeds_for_own_client():
    service, _, client_repository, assignment_repository = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    client_repository.seed(client, "client@example.com")

    detail = asyncio.run(
        service.create_check_in(
            actor_role=RoleName.CLIENT,
            actor_id=client_user_id,
            **_create_kwargs(client.id, mood=4, workout_completed=True),
        )
    )

    assert detail.client_id == client.id
    assert detail.submitted_by == client_user_id
    assert detail.mood == 4


def test_create_check_in_rejects_client_submitting_for_another_client():
    service, _, client_repository, assignment_repository = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    client_repository.seed(other_client, "other@example.com")

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.create_check_in(
                actor_role=RoleName.CLIENT,
                actor_id=client_user_id,
                **_create_kwargs(other_client.id, mood=4),
            )
        )


def test_create_check_in_rejects_empty_payload():
    service, _, client_repository, assignment_repository = _make_service()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)

    with pytest.raises(CheckInFieldsRequiredError):
        asyncio.run(
            service.create_check_in(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                **_create_kwargs(client.id),
            )
        )


def test_create_check_in_raises_when_client_missing():
    service, *_ = _make_service()

    with pytest.raises(ClientNotFoundError):
        asyncio.run(
            service.create_check_in(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                **_create_kwargs(uuid.uuid4(), mood=3),
            )
        )


def test_create_check_in_raises_when_trainer_profile_missing():
    service, _, client_repository, assignment_repository = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")

    with pytest.raises(TrainerNotFoundError):
        asyncio.run(
            service.create_check_in(
                actor_role=RoleName.TRAINER,
                actor_id=uuid.uuid4(),
                **_create_kwargs(client.id, mood=3),
            )
        )


def test_create_check_in_prevents_duplicate_for_same_calendar_day():
    service, _, client_repository, assignment_repository = _make_service()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    today_noon = datetime.now(timezone.utc).replace(
        hour=12, minute=0, second=0, microsecond=0
    )

    asyncio.run(
        service.create_check_in(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            **_create_kwargs(client.id, submitted_at=today_noon, mood=3),
        )
    )

    with pytest.raises(DuplicateCheckInError):
        asyncio.run(
            service.create_check_in(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                **_create_kwargs(
                    client.id, submitted_at=today_noon + timedelta(hours=2), mood=5
                ),
            )
        )


def test_create_check_in_allows_second_check_in_on_a_different_day():
    service, _, client_repository, assignment_repository = _make_service()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    today_noon = datetime.now(timezone.utc).replace(
        hour=12, minute=0, second=0, microsecond=0
    )

    asyncio.run(
        service.create_check_in(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            **_create_kwargs(client.id, submitted_at=today_noon, mood=3),
        )
    )

    detail = asyncio.run(
        service.create_check_in(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            **_create_kwargs(
                client.id, submitted_at=today_noon + timedelta(days=1), mood=5
            ),
        )
    )

    assert detail.mood == 5


# --- list_check_ins -------------------------------------------------------------


def test_list_check_ins_returns_all_for_super_admin():
    service, check_in_repository, *_ = _make_service()
    for _ in range(3):
        check_in_repository.seed(_make_check_in(uuid.uuid4(), uuid.uuid4()))

    result = asyncio.run(
        service.list_check_ins(
            actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), page=1, page_size=2
        )
    )

    assert result.total == 3
    assert len(result.items) == 2


def test_list_check_ins_returns_only_assigned_clients_for_trainer():
    service, check_in_repository, client_repository, assignment_repository = _make_service()
    client, trainer, trainer_user_id = _setup_assigned_pair(
        client_repository, assignment_repository
    )
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(other_client, "other@example.com")
    check_in_repository.seed(_make_check_in(client.id, trainer.id))
    check_in_repository.seed(_make_check_in(other_client.id, uuid.uuid4()))

    result = asyncio.run(
        service.list_check_ins(
            actor_role=RoleName.TRAINER, actor_id=trainer_user_id, page=1, page_size=20
        )
    )

    assert result.total == 1
    assert result.items[0].client_id == client.id


def test_list_check_ins_returns_only_own_for_client():
    service, check_in_repository, client_repository, _ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    check_in_repository.seed(_make_check_in(client.id, uuid.uuid4()))
    check_in_repository.seed(_make_check_in(other_client.id, uuid.uuid4()))

    result = asyncio.run(
        service.list_check_ins(
            actor_role=RoleName.CLIENT, actor_id=client_user_id, page=1, page_size=20
        )
    )

    assert result.total == 1
    assert result.items[0].client_id == client.id


# --- get_check_in / view access -------------------------------------------------


def test_get_check_in_succeeds_for_owning_client():
    service, check_in_repository, client_repository, _ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    client_repository.seed(client, "client@example.com")
    check_in = _make_check_in(client.id, uuid.uuid4())
    check_in_repository.seed(check_in)

    detail = asyncio.run(
        service.get_check_in(
            actor_role=RoleName.CLIENT, actor_id=client_user_id, check_in_id=check_in.id
        )
    )

    assert detail.id == check_in.id


def test_get_check_in_rejects_non_owning_client():
    service, check_in_repository, client_repository, _ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    client_repository.seed(client, "client@example.com")
    check_in = _make_check_in(uuid.uuid4(), uuid.uuid4())
    check_in_repository.seed(check_in)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_check_in(
                actor_role=RoleName.CLIENT, actor_id=client_user_id, check_in_id=check_in.id
            )
        )


def test_get_check_in_rejects_non_assigned_trainer():
    service, check_in_repository, client_repository, assignment_repository = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    check_in = _make_check_in(uuid.uuid4(), uuid.uuid4())
    check_in_repository.seed(check_in)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_check_in(
                actor_role=RoleName.TRAINER,
                actor_id=trainer_user_id,
                check_in_id=check_in.id,
            )
        )


def test_get_check_in_raises_not_found():
    service, *_ = _make_service()

    with pytest.raises(CheckInNotFoundError):
        asyncio.run(
            service.get_check_in(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                check_in_id=uuid.uuid4(),
            )
        )


# --- get_client_check_ins (historical records) ----------------------------------


def test_get_client_check_ins_preserves_full_history():
    service, check_in_repository, client_repository, assignment_repository = _make_service()
    client, trainer, trainer_user_id = _setup_assigned_pair(
        client_repository, assignment_repository
    )
    now = datetime.now(timezone.utc)
    first = _make_check_in(client.id, trainer.id, mood=3, submitted_at=now - timedelta(days=2))
    second = _make_check_in(client.id, trainer.id, mood=4, submitted_at=now - timedelta(days=1))
    third = _make_check_in(client.id, trainer.id, mood=5, submitted_at=now)
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
    service, _, client_repository, _ = _make_service()
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


# --- get_latest_check_in ---------------------------------------------------------


def test_get_latest_check_in_returns_most_recent():
    service, check_in_repository, client_repository, assignment_repository = _make_service()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    now = datetime.now(timezone.utc)
    older = _make_check_in(client.id, trainer.id, mood=3, submitted_at=now - timedelta(days=1))
    newest = _make_check_in(client.id, trainer.id, mood=5, submitted_at=now)
    check_in_repository.seed(older)
    check_in_repository.seed(newest)

    latest = asyncio.run(
        service.get_latest_check_in(
            actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), client_id=client.id
        )
    )

    assert latest.mood == 5


def test_get_latest_check_in_raises_not_found_without_any_check_ins():
    service, _, client_repository, assignment_repository = _make_service()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)

    with pytest.raises(CheckInNotFoundError):
        asyncio.run(
            service.get_latest_check_in(
                actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), client_id=client.id
            )
        )
