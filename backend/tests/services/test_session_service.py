import asyncio
import uuid
from datetime import date, datetime, time, timedelta, timezone

import pytest

from core.constants import RoleName
from models.client_trainer_assignment import ClientTrainerAssignment
from models.session import Session, SessionAttendanceStatus, SessionMeetingType, SessionStatus
from models.subscription import SubscriptionStatus
from repositories.session_repository import SessionRepository
from services.session_service import (
    AttendanceImmutableError,
    ClientNotFoundError,
    ClientOverlapError,
    ForbiddenError,
    SessionInPastError,
    SessionLimitReachedError,
    SessionNotFoundError,
    SessionService,
    SubscriptionNotEligibleError,
    TrainerNotAssignedError,
    TrainerNotFoundError,
    TrainerOverlapError,
)
from tests.services.test_assignment_service import FakeAssignmentRepository, _make_trainer
from tests.services.test_client_service import FakeClientRepository, _make_client
from tests.services.test_subscription_plan_service import FakeSubscriptionPlanRepository, _make_plan
from tests.services.test_subscription_service import FakeSubscriptionRepository, _make_subscription


class FakeSessionRepository(SessionRepository):
    def __init__(self) -> None:
        self._sessions: dict[uuid.UUID, Session] = {}

    def seed(self, session: Session) -> None:
        self._sessions[session.id] = session

    async def create(self, session: Session) -> Session:
        now = datetime.now(timezone.utc)
        session.id = session.id or uuid.uuid4()
        session.created_at = now
        session.updated_at = now
        self._sessions[session.id] = session
        return session

    async def get_by_id(self, session_id: uuid.UUID) -> Session | None:
        return self._sessions.get(session_id)

    async def update(self, session_id: uuid.UUID, values: dict) -> Session | None:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        for key, value in values.items():
            setattr(session, key, value)
        session.updated_at = datetime.now(timezone.utc)
        return session

    async def list_paginated(self, offset: int, limit: int) -> tuple[list[Session], int]:
        ordered = sorted(
            self._sessions.values(), key=lambda s: s.scheduled_start, reverse=True
        )
        return ordered[offset : offset + limit], len(ordered)

    async def list_for_trainer(
        self, trainer_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[Session], int]:
        matched = [s for s in self._sessions.values() if s.trainer_id == trainer_id]
        ordered = sorted(matched, key=lambda s: s.scheduled_start, reverse=True)
        return ordered[offset : offset + limit], len(ordered)

    async def list_for_client(
        self, client_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[Session], int]:
        matched = [s for s in self._sessions.values() if s.client_id == client_id]
        ordered = sorted(matched, key=lambda s: s.scheduled_start, reverse=True)
        return ordered[offset : offset + limit], len(ordered)

    async def list_all_for_client(self, client_id: uuid.UUID) -> list[Session]:
        matched = [s for s in self._sessions.values() if s.client_id == client_id]
        return sorted(matched, key=lambda s: s.scheduled_start, reverse=True)

    async def trainer_has_overlap(
        self, trainer_id: uuid.UUID, start: datetime, end: datetime
    ) -> bool:
        return any(
            s.trainer_id == trainer_id
            and s.status != SessionStatus.CANCELLED
            and s.scheduled_start < end
            and s.scheduled_end > start
            for s in self._sessions.values()
        )

    async def client_has_overlap(
        self, client_id: uuid.UUID, start: datetime, end: datetime
    ) -> bool:
        return any(
            s.client_id == client_id
            and s.status != SessionStatus.CANCELLED
            and s.scheduled_start < end
            and s.scheduled_end > start
            for s in self._sessions.values()
        )

    async def count_active_for_client(self, client_id: uuid.UUID) -> int:
        return sum(
            1
            for s in self._sessions.values()
            if s.client_id == client_id
            and s.status
            in (SessionStatus.SCHEDULED, SessionStatus.COMPLETED, SessionStatus.RESCHEDULED)
        )

    async def count_in_range(
        self,
        start: datetime,
        end: datetime,
        *,
        trainer_id: uuid.UUID | None = None,
        client_id: uuid.UUID | None = None,
        exclude_cancelled: bool = False,
    ) -> int:
        return sum(
            1
            for s in self._sessions.values()
            if start <= s.scheduled_start < end
            and (trainer_id is None or s.trainer_id == trainer_id)
            and (client_id is None or s.client_id == client_id)
            and (not exclude_cancelled or s.status != SessionStatus.CANCELLED)
        )


def _make_session(client_id: uuid.UUID, trainer_id: uuid.UUID, **overrides) -> Session:
    now = datetime.now(timezone.utc)
    start = now + timedelta(days=1)
    defaults = dict(
        id=uuid.uuid4(),
        client_id=client_id,
        trainer_id=trainer_id,
        scheduled_start=start,
        scheduled_end=start + timedelta(minutes=60),
        duration_minutes=60,
        status=SessionStatus.SCHEDULED,
        meeting_type=SessionMeetingType.GOOGLE_MEET,
        meeting_link=None,
        trainer_notes=None,
        trainer_feedback=None,
        homework=None,
        next_session_focus=None,
        attendance_status=None,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return Session(**defaults)


def _make_service() -> tuple[
    SessionService,
    FakeSessionRepository,
    FakeClientRepository,
    FakeAssignmentRepository,
    FakeSubscriptionRepository,
    FakeSubscriptionPlanRepository,
]:
    session_repository = FakeSessionRepository()
    client_repository = FakeClientRepository()
    assignment_repository = FakeAssignmentRepository()
    subscription_repository = FakeSubscriptionRepository()
    subscription_plan_repository = FakeSubscriptionPlanRepository()
    service = SessionService(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        subscription_plan_repository,
    )
    return (
        service,
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        subscription_plan_repository,
    )


def _setup_eligible_pair(
    client_repository: FakeClientRepository,
    assignment_repository: FakeAssignmentRepository,
    subscription_repository: FakeSubscriptionRepository,
    subscription_plan_repository: FakeSubscriptionPlanRepository,
    max_sessions_per_month: int | None = 12,
):
    client = _make_client(user_id=uuid.uuid4())
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    client_repository.seed(client, "client@example.com")
    assignment_repository.seed_trainer(trainer)
    assignment_repository.seed_assignment(
        ClientTrainerAssignment(
            id=uuid.uuid4(), client_id=client.id, trainer_id=trainer.id, is_primary=True
        )
    )
    plan = _make_plan(max_sessions_per_month=max_sessions_per_month)
    subscription_plan_repository.seed(plan)
    subscription_repository.seed(
        _make_subscription(
            client.id,
            plan.id,
            status=SubscriptionStatus.ACTIVE,
            end_date=date.today() + timedelta(days=30),
        )
    )
    return client, trainer, trainer_user_id


def _future_start(days: int = 1) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=days)


# --- create_session ---------------------------------------------------------


def test_create_session_succeeds_for_super_admin():
    service, _, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_service()
    )
    client, trainer, _ = _setup_eligible_pair(
        client_repository, assignment_repository, subscription_repository, plan_repository
    )

    detail = asyncio.run(
        service.create_session(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            client_id=client.id,
            trainer_id=trainer.id,
            scheduled_start=_future_start(),
            duration_minutes=60,
            meeting_type=SessionMeetingType.GOOGLE_MEET,
            meeting_link=None,
            trainer_notes=None,
        )
    )

    assert detail.client_id == client.id
    assert detail.trainer_id == trainer.id
    assert detail.status == SessionStatus.SCHEDULED


def test_create_session_succeeds_for_assigned_trainer_without_trainer_id():
    service, _, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_service()
    )
    client, trainer, trainer_user_id = _setup_eligible_pair(
        client_repository, assignment_repository, subscription_repository, plan_repository
    )

    detail = asyncio.run(
        service.create_session(
            actor_role=RoleName.TRAINER,
            actor_id=trainer_user_id,
            client_id=client.id,
            trainer_id=None,
            scheduled_start=_future_start(),
            duration_minutes=60,
            meeting_type=SessionMeetingType.ZOOM,
            meeting_link=None,
            trainer_notes=None,
        )
    )

    assert detail.trainer_id == trainer.id


def test_create_session_rejects_non_trainer_admin_role():
    service, *_ = _make_service()

    for role in (RoleName.CLIENT, None):
        with pytest.raises(ForbiddenError):
            asyncio.run(
                service.create_session(
                    actor_role=role,
                    actor_id=uuid.uuid4(),
                    client_id=uuid.uuid4(),
                    trainer_id=uuid.uuid4(),
                    scheduled_start=_future_start(),
                    duration_minutes=60,
                    meeting_type=SessionMeetingType.GOOGLE_MEET,
                    meeting_link=None,
                    trainer_notes=None,
                )
            )


def test_create_session_raises_when_client_missing():
    service, *_ = _make_service()

    with pytest.raises(ClientNotFoundError):
        asyncio.run(
            service.create_session(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                client_id=uuid.uuid4(),
                trainer_id=uuid.uuid4(),
                scheduled_start=_future_start(),
                duration_minutes=60,
                meeting_type=SessionMeetingType.GOOGLE_MEET,
                meeting_link=None,
                trainer_notes=None,
            )
        )


def test_create_session_raises_when_trainer_missing_for_super_admin():
    service, _, client_repository, *_ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")

    with pytest.raises(TrainerNotFoundError):
        asyncio.run(
            service.create_session(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                client_id=client.id,
                trainer_id=None,
                scheduled_start=_future_start(),
                duration_minutes=60,
                meeting_type=SessionMeetingType.GOOGLE_MEET,
                meeting_link=None,
                trainer_notes=None,
            )
        )


def test_create_session_raises_when_trainer_not_assigned_to_client():
    service, _, client_repository, assignment_repository, *_ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    trainer = _make_trainer(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    assignment_repository.seed_trainer(trainer)
    # Note: no assignment created between trainer and client.

    with pytest.raises(TrainerNotAssignedError):
        asyncio.run(
            service.create_session(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                client_id=client.id,
                trainer_id=trainer.id,
                scheduled_start=_future_start(),
                duration_minutes=60,
                meeting_type=SessionMeetingType.GOOGLE_MEET,
                meeting_link=None,
                trainer_notes=None,
            )
        )


def test_create_session_rejects_trainer_creating_for_another_trainer():
    service, _, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_service()
    )
    client, trainer, _ = _setup_eligible_pair(
        client_repository, assignment_repository, subscription_repository, plan_repository
    )
    other_trainer_user_id = uuid.uuid4()
    other_trainer = _make_trainer(user_id=other_trainer_user_id)
    assignment_repository.seed_trainer(other_trainer)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.create_session(
                actor_role=RoleName.TRAINER,
                actor_id=other_trainer_user_id,
                client_id=client.id,
                trainer_id=trainer.id,
                scheduled_start=_future_start(),
                duration_minutes=60,
                meeting_type=SessionMeetingType.GOOGLE_MEET,
                meeting_link=None,
                trainer_notes=None,
            )
        )


def test_create_session_raises_when_subscription_not_eligible():
    service, _, client_repository, assignment_repository, _, plan_repository = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    trainer = _make_trainer(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    assignment_repository.seed_trainer(trainer)
    assignment_repository.seed_assignment(
        ClientTrainerAssignment(
            id=uuid.uuid4(), client_id=client.id, trainer_id=trainer.id, is_primary=True
        )
    )
    # Note: no active subscription seeded for the client.

    with pytest.raises(SubscriptionNotEligibleError):
        asyncio.run(
            service.create_session(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                client_id=client.id,
                trainer_id=trainer.id,
                scheduled_start=_future_start(),
                duration_minutes=60,
                meeting_type=SessionMeetingType.GOOGLE_MEET,
                meeting_link=None,
                trainer_notes=None,
            )
        )


def test_create_session_raises_when_scheduled_in_the_past():
    service, _, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_service()
    )
    client, trainer, _ = _setup_eligible_pair(
        client_repository, assignment_repository, subscription_repository, plan_repository
    )

    with pytest.raises(SessionInPastError):
        asyncio.run(
            service.create_session(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                client_id=client.id,
                trainer_id=trainer.id,
                scheduled_start=datetime.now(timezone.utc) - timedelta(days=1),
                duration_minutes=60,
                meeting_type=SessionMeetingType.GOOGLE_MEET,
                meeting_link=None,
                trainer_notes=None,
            )
        )


def test_create_session_raises_on_client_overlap():
    service, session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_service()
    )
    client, trainer, _ = _setup_eligible_pair(
        client_repository, assignment_repository, subscription_repository, plan_repository
    )
    other_trainer_user_id = uuid.uuid4()
    other_trainer = _make_trainer(user_id=other_trainer_user_id)
    assignment_repository.seed_trainer(other_trainer)
    assignment_repository.seed_assignment(
        ClientTrainerAssignment(
            id=uuid.uuid4(), client_id=client.id, trainer_id=other_trainer.id, is_primary=False
        )
    )
    existing_start = _future_start(days=2).replace(hour=19, minute=0, second=0, microsecond=0)
    session_repository.seed(
        _make_session(
            client.id,
            other_trainer.id,
            scheduled_start=existing_start,
            scheduled_end=existing_start + timedelta(hours=1),
        )
    )

    with pytest.raises(ClientOverlapError):
        asyncio.run(
            service.create_session(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                client_id=client.id,
                trainer_id=trainer.id,
                scheduled_start=existing_start + timedelta(minutes=30),
                duration_minutes=60,
                meeting_type=SessionMeetingType.GOOGLE_MEET,
                meeting_link=None,
                trainer_notes=None,
            )
        )


def test_create_session_raises_on_trainer_overlap():
    service, session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_service()
    )
    client, trainer, _ = _setup_eligible_pair(
        client_repository, assignment_repository, subscription_repository, plan_repository
    )
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(other_client, "other@example.com")
    assignment_repository.seed_assignment(
        ClientTrainerAssignment(
            id=uuid.uuid4(), client_id=other_client.id, trainer_id=trainer.id, is_primary=False
        )
    )
    existing_start = _future_start(days=2).replace(hour=19, minute=0, second=0, microsecond=0)
    session_repository.seed(
        _make_session(
            other_client.id,
            trainer.id,
            scheduled_start=existing_start,
            scheduled_end=existing_start + timedelta(hours=1),
        )
    )

    with pytest.raises(TrainerOverlapError):
        asyncio.run(
            service.create_session(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                client_id=client.id,
                trainer_id=trainer.id,
                scheduled_start=existing_start + timedelta(minutes=30),
                duration_minutes=60,
                meeting_type=SessionMeetingType.GOOGLE_MEET,
                meeting_link=None,
                trainer_notes=None,
            )
        )


def test_create_session_allows_back_to_back_non_overlapping_slots():
    service, _, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_service()
    )
    client, trainer, _ = _setup_eligible_pair(
        client_repository, assignment_repository, subscription_repository, plan_repository
    )
    first_start = _future_start(days=2).replace(hour=19, minute=0, second=0, microsecond=0)

    asyncio.run(
        service.create_session(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            client_id=client.id,
            trainer_id=trainer.id,
            scheduled_start=first_start,
            duration_minutes=60,
            meeting_type=SessionMeetingType.GOOGLE_MEET,
            meeting_link=None,
            trainer_notes=None,
        )
    )

    # 8 PM - 9 PM immediately after a 7 PM - 8 PM session is valid (touching, not overlapping).
    detail = asyncio.run(
        service.create_session(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            client_id=client.id,
            trainer_id=trainer.id,
            scheduled_start=first_start + timedelta(hours=1),
            duration_minutes=60,
            meeting_type=SessionMeetingType.GOOGLE_MEET,
            meeting_link=None,
            trainer_notes=None,
        )
    )

    assert detail.scheduled_start == first_start + timedelta(hours=1)


def test_create_session_raises_when_session_limit_reached():
    service, _, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_service()
    )
    client, trainer, _ = _setup_eligible_pair(
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        max_sessions_per_month=1,
    )
    asyncio.run(
        service.create_session(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            client_id=client.id,
            trainer_id=trainer.id,
            scheduled_start=_future_start(days=1),
            duration_minutes=60,
            meeting_type=SessionMeetingType.GOOGLE_MEET,
            meeting_link=None,
            trainer_notes=None,
        )
    )

    with pytest.raises(SessionLimitReachedError):
        asyncio.run(
            service.create_session(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                client_id=client.id,
                trainer_id=trainer.id,
                scheduled_start=_future_start(days=2),
                duration_minutes=60,
                meeting_type=SessionMeetingType.GOOGLE_MEET,
                meeting_link=None,
                trainer_notes=None,
            )
        )


# --- remaining_sessions ------------------------------------------------------


def test_remaining_sessions_returns_zero_without_active_subscription():
    service, *_ = _make_service()

    remaining = asyncio.run(service.remaining_sessions(uuid.uuid4()))

    assert remaining == 0


def test_remaining_sessions_returns_none_for_unlimited_plan():
    service, _, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_service()
    )
    client, _, _ = _setup_eligible_pair(
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        max_sessions_per_month=None,
    )

    remaining = asyncio.run(service.remaining_sessions(client.id))

    assert remaining is None


def test_remaining_sessions_accounts_for_existing_active_sessions():
    service, session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_service()
    )
    client, trainer, _ = _setup_eligible_pair(
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        max_sessions_per_month=12,
    )
    for status in (SessionStatus.COMPLETED,) * 8 + (SessionStatus.SCHEDULED,) * 2:
        session_repository.seed(_make_session(client.id, trainer.id, status=status))
    session_repository.seed(
        _make_session(client.id, trainer.id, status=SessionStatus.CANCELLED)
    )

    remaining = asyncio.run(service.remaining_sessions(client.id))

    assert remaining == 2


# --- bulk_create_sessions ----------------------------------------------------


def test_bulk_create_sessions_creates_and_skips_at_limit():
    service, _, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_service()
    )
    client, trainer, _ = _setup_eligible_pair(
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        max_sessions_per_month=12,
    )

    result = asyncio.run(
        service.bulk_create_sessions(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            client_id=client.id,
            trainer_id=trainer.id,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
            days=["MONDAY", "WEDNESDAY", "FRIDAY"],
            start_time=time(19, 0),
            duration_minutes=60,
            meeting_type=SessionMeetingType.GOOGLE_MEET,
        )
    )

    assert result.sessions_created == 12
    assert result.sessions_skipped == 1
    assert len(result.skipped_reasons) == 1
    assert "maximum number of sessions" in result.skipped_reasons[0]


def test_bulk_create_sessions_skips_trainer_overlap_and_continues():
    service, session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_service()
    )
    client, trainer, _ = _setup_eligible_pair(
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        max_sessions_per_month=None,
    )
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(other_client, "other@example.com")
    assignment_repository.seed_assignment(
        ClientTrainerAssignment(
            id=uuid.uuid4(), client_id=other_client.id, trainer_id=trainer.id, is_primary=False
        )
    )
    # Occupies the trainer at 19:00 IST on Monday 2026-08-03.
    conflicting_start = datetime(2026, 8, 3, 13, 30, tzinfo=timezone.utc)
    session_repository.seed(
        _make_session(
            other_client.id,
            trainer.id,
            scheduled_start=conflicting_start,
            scheduled_end=conflicting_start + timedelta(hours=1),
        )
    )

    result = asyncio.run(
        service.bulk_create_sessions(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            client_id=client.id,
            trainer_id=trainer.id,
            start_date=date(2026, 8, 3),
            end_date=date(2026, 8, 3),
            days=["MONDAY"],
            start_time=time(19, 0),
            duration_minutes=60,
            meeting_type=SessionMeetingType.GOOGLE_MEET,
        )
    )

    assert result.sessions_created == 0
    assert result.sessions_skipped == 1
    assert "Trainer has an overlapping session" in result.skipped_reasons[0]


def test_bulk_create_sessions_rejects_non_trainer_admin_role():
    service, *_ = _make_service()

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.bulk_create_sessions(
                actor_role=RoleName.CLIENT,
                actor_id=uuid.uuid4(),
                client_id=uuid.uuid4(),
                trainer_id=uuid.uuid4(),
                start_date=date(2026, 8, 1),
                end_date=date(2026, 8, 31),
                days=["MONDAY"],
                start_time=time(19, 0),
                duration_minutes=60,
                meeting_type=SessionMeetingType.GOOGLE_MEET,
            )
        )


# --- list_sessions / list_my_sessions ---------------------------------------


def test_list_sessions_returns_all_for_super_admin():
    service, session_repository, *_ = _make_service()
    for _ in range(3):
        session_repository.seed(_make_session(uuid.uuid4(), uuid.uuid4()))

    result = asyncio.run(
        service.list_sessions(actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), page=1, page_size=2)
    )

    assert result.total == 3
    assert len(result.items) == 2


def test_list_sessions_returns_only_assigned_for_trainer():
    service, session_repository, _, assignment_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    other_trainer = _make_trainer(user_id=uuid.uuid4())
    assignment_repository.seed_trainer(trainer)
    session_repository.seed(_make_session(uuid.uuid4(), trainer.id))
    session_repository.seed(_make_session(uuid.uuid4(), other_trainer.id))

    result = asyncio.run(
        service.list_sessions(
            actor_role=RoleName.TRAINER, actor_id=trainer_user_id, page=1, page_size=20
        )
    )

    assert result.total == 1
    assert result.items[0].trainer_id == trainer.id


def test_list_sessions_returns_only_own_for_client():
    service, session_repository, client_repository, *_ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    session_repository.seed(_make_session(client.id, uuid.uuid4()))
    session_repository.seed(_make_session(other_client.id, uuid.uuid4()))

    result = asyncio.run(
        service.list_sessions(actor_role=RoleName.CLIENT, actor_id=client_user_id, page=1, page_size=20)
    )

    assert result.total == 1
    assert result.items[0].client_id == client.id


def test_list_my_sessions_rejects_non_client():
    service, *_ = _make_service()

    with pytest.raises(ForbiddenError):
        asyncio.run(service.list_my_sessions(actor_role=RoleName.TRAINER, actor_id=uuid.uuid4()))


def test_list_my_sessions_returns_only_own_sessions():
    service, session_repository, client_repository, *_ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    client_repository.seed(client, "client@example.com")
    session_repository.seed(_make_session(client.id, uuid.uuid4()))
    session_repository.seed(_make_session(uuid.uuid4(), uuid.uuid4()))

    items = asyncio.run(service.list_my_sessions(actor_role=RoleName.CLIENT, actor_id=client_user_id))

    assert len(items) == 1
    assert items[0].client_id == client.id


# --- get_session -------------------------------------------------------------


def test_get_session_succeeds_for_super_admin():
    service, session_repository, *_ = _make_service()
    session = _make_session(uuid.uuid4(), uuid.uuid4())
    session_repository.seed(session)

    detail = asyncio.run(
        service.get_session(actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), session_id=session.id)
    )

    assert detail.id == session.id


def test_get_session_succeeds_for_owning_trainer():
    service, session_repository, _, assignment_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    session = _make_session(uuid.uuid4(), trainer.id)
    session_repository.seed(session)

    detail = asyncio.run(
        service.get_session(actor_role=RoleName.TRAINER, actor_id=trainer_user_id, session_id=session.id)
    )

    assert detail.id == session.id


def test_get_session_rejects_non_owning_trainer():
    service, session_repository, _, assignment_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    session = _make_session(uuid.uuid4(), uuid.uuid4())
    session_repository.seed(session)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_session(
                actor_role=RoleName.TRAINER, actor_id=trainer_user_id, session_id=session.id
            )
        )


def test_get_session_succeeds_for_owning_client():
    service, session_repository, client_repository, *_ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    client_repository.seed(client, "client@example.com")
    session = _make_session(client.id, uuid.uuid4())
    session_repository.seed(session)

    detail = asyncio.run(
        service.get_session(actor_role=RoleName.CLIENT, actor_id=client_user_id, session_id=session.id)
    )

    assert detail.id == session.id


def test_get_session_rejects_non_owning_client():
    service, session_repository, client_repository, *_ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    client_repository.seed(client, "client@example.com")
    session = _make_session(uuid.uuid4(), uuid.uuid4())
    session_repository.seed(session)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_session(
                actor_role=RoleName.CLIENT, actor_id=client_user_id, session_id=session.id
            )
        )


def test_get_session_raises_not_found():
    service, *_ = _make_service()

    with pytest.raises(SessionNotFoundError):
        asyncio.run(
            service.get_session(
                actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), session_id=uuid.uuid4()
            )
        )


# --- update_session ----------------------------------------------------------


def test_update_session_succeeds_for_super_admin():
    service, session_repository, *_ = _make_service()
    session = _make_session(uuid.uuid4(), uuid.uuid4())
    session_repository.seed(session)

    detail = asyncio.run(
        service.update_session(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            session_id=session.id,
            values={"status": SessionStatus.COMPLETED, "trainer_notes": "Great session."},
        )
    )

    assert detail.status == SessionStatus.COMPLETED
    assert detail.trainer_notes == "Great session."


def test_update_session_succeeds_for_owning_trainer():
    service, session_repository, _, assignment_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    session = _make_session(uuid.uuid4(), trainer.id)
    session_repository.seed(session)

    detail = asyncio.run(
        service.update_session(
            actor_role=RoleName.TRAINER,
            actor_id=trainer_user_id,
            session_id=session.id,
            values={"status": SessionStatus.CANCELLED},
        )
    )

    assert detail.status == SessionStatus.CANCELLED


def test_update_session_rejects_non_owning_trainer():
    service, session_repository, _, assignment_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    session = _make_session(uuid.uuid4(), uuid.uuid4())
    session_repository.seed(session)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.update_session(
                actor_role=RoleName.TRAINER,
                actor_id=trainer_user_id,
                session_id=session.id,
                values={"status": SessionStatus.CANCELLED},
            )
        )


def test_update_session_rejects_client_role():
    service, session_repository, *_ = _make_service()
    session = _make_session(uuid.uuid4(), uuid.uuid4())
    session_repository.seed(session)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.update_session(
                actor_role=RoleName.CLIENT,
                actor_id=uuid.uuid4(),
                session_id=session.id,
                values={"status": SessionStatus.CANCELLED},
            )
        )


def test_update_session_raises_not_found():
    service, *_ = _make_service()

    with pytest.raises(SessionNotFoundError):
        asyncio.run(
            service.update_session(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                session_id=uuid.uuid4(),
                values={"status": SessionStatus.CANCELLED},
            )
        )


# --- update_session_notes -----------------------------------------------------


def test_update_session_notes_succeeds_for_owning_trainer():
    service, session_repository, _, assignment_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    session = _make_session(uuid.uuid4(), trainer.id)
    session_repository.seed(session)

    detail = asyncio.run(
        service.update_session_notes(
            actor_role=RoleName.TRAINER,
            actor_id=trainer_user_id,
            session_id=session.id,
            values={
                "trainer_notes": "Improved endurance.",
                "trainer_feedback": "Consistency improving.",
                "homework": "Walk 10,000 steps daily.",
                "next_session_focus": "Core strengthening.",
            },
        )
    )

    assert detail.trainer_notes == "Improved endurance."
    assert detail.trainer_feedback == "Consistency improving."
    assert detail.homework == "Walk 10,000 steps daily."
    assert detail.next_session_focus == "Core strengthening."


def test_update_session_notes_succeeds_for_super_admin():
    service, session_repository, *_ = _make_service()
    session = _make_session(uuid.uuid4(), uuid.uuid4())
    session_repository.seed(session)

    detail = asyncio.run(
        service.update_session_notes(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            session_id=session.id,
            values={"homework": "Stretch daily."},
        )
    )

    assert detail.homework == "Stretch daily."


def test_update_session_notes_rejects_non_owning_trainer():
    service, session_repository, _, assignment_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    session = _make_session(uuid.uuid4(), uuid.uuid4())
    session_repository.seed(session)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.update_session_notes(
                actor_role=RoleName.TRAINER,
                actor_id=trainer_user_id,
                session_id=session.id,
                values={"trainer_notes": "Should not be applied."},
            )
        )


def test_update_session_notes_rejects_client_role():
    service, session_repository, *_ = _make_service()
    session = _make_session(uuid.uuid4(), uuid.uuid4())
    session_repository.seed(session)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.update_session_notes(
                actor_role=RoleName.CLIENT,
                actor_id=uuid.uuid4(),
                session_id=session.id,
                values={"trainer_notes": "Should not be applied."},
            )
        )


def test_update_session_notes_raises_not_found():
    service, *_ = _make_service()

    with pytest.raises(SessionNotFoundError):
        asyncio.run(
            service.update_session_notes(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                session_id=uuid.uuid4(),
                values={"homework": "Stretch daily."},
            )
        )


# --- update_session_attendance -------------------------------------------------


def test_update_session_attendance_succeeds_for_owning_trainer():
    service, session_repository, _, assignment_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    session = _make_session(uuid.uuid4(), trainer.id)
    session_repository.seed(session)

    detail = asyncio.run(
        service.update_session_attendance(
            actor_role=RoleName.TRAINER,
            actor_id=trainer_user_id,
            session_id=session.id,
            attendance_status=SessionAttendanceStatus.BOTH_PRESENT,
        )
    )

    assert detail.attendance_status == SessionAttendanceStatus.BOTH_PRESENT


def test_update_session_attendance_succeeds_for_super_admin():
    service, session_repository, *_ = _make_service()
    session = _make_session(uuid.uuid4(), uuid.uuid4())
    session_repository.seed(session)

    detail = asyncio.run(
        service.update_session_attendance(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=uuid.uuid4(),
            session_id=session.id,
            attendance_status=SessionAttendanceStatus.LATE,
        )
    )

    assert detail.attendance_status == SessionAttendanceStatus.LATE


def test_update_session_attendance_rejects_non_owning_trainer():
    service, session_repository, _, assignment_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    session = _make_session(uuid.uuid4(), uuid.uuid4())
    session_repository.seed(session)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.update_session_attendance(
                actor_role=RoleName.TRAINER,
                actor_id=trainer_user_id,
                session_id=session.id,
                attendance_status=SessionAttendanceStatus.PRESENT,
            )
        )


def test_update_session_attendance_rejects_client_role():
    service, session_repository, *_ = _make_service()
    session = _make_session(uuid.uuid4(), uuid.uuid4())
    session_repository.seed(session)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.update_session_attendance(
                actor_role=RoleName.CLIENT,
                actor_id=uuid.uuid4(),
                session_id=session.id,
                attendance_status=SessionAttendanceStatus.PRESENT,
            )
        )


def test_update_session_attendance_rejects_once_completed():
    service, session_repository, *_ = _make_service()
    session = _make_session(uuid.uuid4(), uuid.uuid4(), status=SessionStatus.COMPLETED)
    session_repository.seed(session)

    with pytest.raises(AttendanceImmutableError):
        asyncio.run(
            service.update_session_attendance(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                session_id=session.id,
                attendance_status=SessionAttendanceStatus.PRESENT,
            )
        )


def test_update_session_rejects_attendance_change_once_completed_via_generic_patch():
    service, session_repository, *_ = _make_service()
    session = _make_session(uuid.uuid4(), uuid.uuid4(), status=SessionStatus.COMPLETED)
    session_repository.seed(session)

    with pytest.raises(AttendanceImmutableError):
        asyncio.run(
            service.update_session(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                session_id=session.id,
                values={"attendance_status": SessionAttendanceStatus.PRESENT},
            )
        )


def test_update_session_attendance_raises_not_found():
    service, *_ = _make_service()

    with pytest.raises(SessionNotFoundError):
        asyncio.run(
            service.update_session_attendance(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                session_id=uuid.uuid4(),
                attendance_status=SessionAttendanceStatus.PRESENT,
            )
        )


# --- get_session_summary -------------------------------------------------------


def _make_summary_session(client_id: uuid.UUID, trainer_id: uuid.UUID) -> Session:
    return _make_session(
        client_id,
        trainer_id,
        attendance_status=SessionAttendanceStatus.BOTH_PRESENT,
        trainer_notes="Improved endurance.",
        trainer_feedback="Consistency improving.",
        homework="Walk 10,000 steps daily.",
        next_session_focus="Core strengthening.",
    )


def test_get_session_summary_full_for_super_admin():
    service, session_repository, client_repository, *_ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    session = _make_summary_session(client.id, uuid.uuid4())
    session_repository.seed(session)

    summary = asyncio.run(
        service.get_session_summary(
            actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), session_id=session.id
        )
    )

    assert summary["attendance_status"] == "BOTH_PRESENT"
    assert summary["trainer_notes"] == "Improved endurance."
    assert summary["trainer_feedback"] == "Consistency improving."
    assert summary["homework"] == "Walk 10,000 steps daily."
    assert summary["next_session_focus"] == "Core strengthening."
    assert "session_date" in summary


def test_get_session_summary_full_for_owning_trainer():
    service, session_repository, client_repository, assignment_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    session = _make_summary_session(client.id, trainer.id)
    session_repository.seed(session)

    summary = asyncio.run(
        service.get_session_summary(
            actor_role=RoleName.TRAINER, actor_id=trainer_user_id, session_id=session.id
        )
    )

    assert summary["trainer_notes"] == "Improved endurance."
    assert summary["next_session_focus"] == "Core strengthening."


def test_get_session_summary_rejects_non_owning_trainer():
    service, session_repository, client_repository, assignment_repository, *_ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    session = _make_summary_session(client.id, uuid.uuid4())
    session_repository.seed(session)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_session_summary(
                actor_role=RoleName.TRAINER, actor_id=trainer_user_id, session_id=session.id
            )
        )


def test_get_session_summary_client_sees_only_homework():
    service, session_repository, client_repository, *_ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    client_repository.seed(client, "client@example.com")
    session = _make_summary_session(client.id, uuid.uuid4())
    session_repository.seed(session)

    summary = asyncio.run(
        service.get_session_summary(
            actor_role=RoleName.CLIENT, actor_id=client_user_id, session_id=session.id
        )
    )

    assert summary == {
        "session_date": summary["session_date"],
        "attendance_status": "BOTH_PRESENT",
        "homework": "Walk 10,000 steps daily.",
    }
    assert "trainer_notes" not in summary
    assert "trainer_feedback" not in summary
    assert "next_session_focus" not in summary


def test_get_session_summary_rejects_non_owning_client():
    service, session_repository, client_repository, *_ = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    client_repository.seed(client, "client@example.com")
    session = _make_summary_session(uuid.uuid4(), uuid.uuid4())
    session_repository.seed(session)

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_session_summary(
                actor_role=RoleName.CLIENT, actor_id=client_user_id, session_id=session.id
            )
        )


def test_get_session_summary_raises_not_found():
    service, *_ = _make_service()

    with pytest.raises(SessionNotFoundError):
        asyncio.run(
            service.get_session_summary(
                actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), session_id=uuid.uuid4()
            )
        )
