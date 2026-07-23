import asyncio
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from core.constants import RoleName
from models.check_in import CheckIn
from models.client_trainer_assignment import ClientTrainerAssignment
from models.session import Session, SessionStatus
from repositories.dashboard_repository import DashboardRepository
from services.application_setting_service import ApplicationSettingService
from services.dashboard_service import (
    ClientProfileNotFoundError,
    DashboardService,
    ForbiddenError,
    TrainerProfileNotFoundError,
)
from tests.services.test_application_setting_service import (
    FakeApplicationSettingRepository,
    _make_setting,
)
from tests.services.test_assignment_service import FakeAssignmentRepository, _make_trainer
from tests.services.test_check_in_service import FakeCheckInRepository, _make_check_in
from tests.services.test_client_service import FakeClientRepository, _make_client
from tests.services.test_measurement_service import FakeMeasurementRepository, _make_measurement
from tests.services.test_session_service import FakeSessionRepository, _make_session
from tests.services.test_subscription_plan_service import _make_plan
from tests.services.test_subscription_service import FakeSubscriptionRepository, _make_subscription
from utils.dashboard import (
    client_last_n_days_range_utc,
    client_week_range_utc,
    ist_month_range_utc,
    ist_next_days_range_utc,
    ist_today_range_utc,
)
from utils.subscription import current_india_date


class FakeDashboardRepository(DashboardRepository):
    def __init__(self) -> None:
        self._trainer_count = 0
        self._sessions: list[Session] = []
        self._check_ins: list[CheckIn] = []

    def seed_trainer_count(self, count: int) -> None:
        self._trainer_count = count

    def seed_session(self, session: Session) -> None:
        self._sessions.append(session)

    def seed_check_in(self, check_in: CheckIn) -> None:
        self._check_ins.append(check_in)

    async def count_total_trainers(self) -> int:
        return self._trainer_count

    async def count_pending_check_ins(
        self,
        client_ids: list[uuid.UUID] | None,
        day_start: datetime,
        day_end: datetime,
        now: datetime,
    ) -> int:
        count = 0
        for session in self._sessions:
            if session.status == SessionStatus.CANCELLED:
                continue
            if not (day_start <= session.scheduled_start < day_end):
                continue
            if not (session.scheduled_start < now):
                continue
            if client_ids is not None and session.client_id not in client_ids:
                continue
            has_check_in = any(
                check_in.client_id == session.client_id
                and day_start <= check_in.submitted_at < day_end
                for check_in in self._check_ins
            )
            if not has_check_in:
                count += 1
        return count


def _application_setting_service(
    measurement_overdue_days: int = 14, subscription_expired_days: int = 30
) -> ApplicationSettingService:
    repository = FakeApplicationSettingRepository()
    repository.seed(_make_setting(key="measurement_overdue_days", value=str(measurement_overdue_days)))
    repository.seed(
        _make_setting(key="subscription_expired_days", value=str(subscription_expired_days))
    )
    return ApplicationSettingService(repository)


def _make_service(
    *,
    dashboard_repository=None,
    client_repository=None,
    assignment_repository=None,
    session_repository=None,
    check_in_repository=None,
    measurement_repository=None,
    subscription_repository=None,
    application_setting_service=None,
) -> DashboardService:
    return DashboardService(
        dashboard_repository or FakeDashboardRepository(),
        client_repository or FakeClientRepository(),
        assignment_repository or FakeAssignmentRepository(),
        session_repository or FakeSessionRepository(),
        check_in_repository or FakeCheckInRepository(),
        measurement_repository or FakeMeasurementRepository(),
        subscription_repository or FakeSubscriptionRepository(),
        application_setting_service or _application_setting_service(),
    )


def _midpoint(start: datetime, end: datetime) -> datetime:
    return start + (end - start) / 2


# ---------------------------------------------------------------------------
# Forbidden / not-found guard tests
# ---------------------------------------------------------------------------


def test_trainer_dashboard_rejects_non_trainer():
    service = _make_service()
    for role in (RoleName.SUPER_ADMIN, RoleName.CLIENT, None):
        with pytest.raises(ForbiddenError):
            asyncio.run(service.get_trainer_dashboard(actor_role=role, actor_id=uuid.uuid4()))


def test_trainer_dashboard_raises_when_no_trainer_profile():
    service = _make_service()
    with pytest.raises(TrainerProfileNotFoundError):
        asyncio.run(
            service.get_trainer_dashboard(actor_role=RoleName.TRAINER, actor_id=uuid.uuid4())
        )


def test_super_admin_dashboard_rejects_non_super_admin():
    service = _make_service()
    for role in (RoleName.TRAINER, RoleName.CLIENT, None):
        with pytest.raises(ForbiddenError):
            asyncio.run(service.get_super_admin_dashboard(actor_role=role))


def test_client_dashboard_rejects_non_client():
    service = _make_service()
    for role in (RoleName.TRAINER, RoleName.SUPER_ADMIN, None):
        with pytest.raises(ForbiddenError):
            asyncio.run(service.get_client_dashboard(actor_role=role, actor_id=uuid.uuid4()))


def test_client_dashboard_raises_when_no_client_profile():
    service = _make_service()
    with pytest.raises(ClientProfileNotFoundError):
        asyncio.run(
            service.get_client_dashboard(actor_role=RoleName.CLIENT, actor_id=uuid.uuid4())
        )


# ---------------------------------------------------------------------------
# Trainer / Super Admin dashboards share one fixture: two assigned clients,
# one ACTIVE (client_a) and one EXPIRED (client_b), with sessions/check-ins/
# measurements positioned relative to the real current IST day so the test
# is robust no matter when it runs.
# ---------------------------------------------------------------------------


def _build_shared_fixture():
    dashboard_repository = FakeDashboardRepository()
    client_repository = FakeClientRepository()
    assignment_repository = FakeAssignmentRepository()
    session_repository = FakeSessionRepository()
    check_in_repository = FakeCheckInRepository()
    measurement_repository = FakeMeasurementRepository()
    subscription_repository = FakeSubscriptionRepository()

    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    dashboard_repository.seed_trainer_count(1)

    client_a = _make_client(uuid.uuid4())
    client_b = _make_client(uuid.uuid4())
    for client, email in ((client_a, "a@example.com"), (client_b, "b@example.com")):
        assignment_repository.seed_client(client, email)
        client_repository.seed(client, email)

    for client in (client_a, client_b):
        assignment_repository.seed_assignment(
            ClientTrainerAssignment(
                id=uuid.uuid4(),
                client_id=client.id,
                trainer_id=trainer.id,
                is_primary=True,
            )
        )

    today = current_india_date()
    plan = _make_plan()

    # client_a: ACTIVE subscription, recent measurement (not overdue).
    subscription_repository.seed(
        _make_subscription(
            client_a.id, plan.id, start_date=today - timedelta(days=10), end_date=today + timedelta(days=10)
        )
    )
    measurement_repository.seed(
        _make_measurement(client_a.id, uuid.uuid4(), recorded_at=datetime.now(timezone.utc))
    )

    # client_b: EXPIRED subscription (5 days past end_date, within the
    # 30-day grace window), no measurement ever recorded (overdue).
    subscription_repository.seed(
        _make_subscription(
            client_b.id, plan.id, start_date=today - timedelta(days=35), end_date=today - timedelta(days=5)
        )
    )

    today_start, today_end = ist_today_range_utc()
    now = datetime.now(timezone.utc)
    today_session_time = _midpoint(today_start, now)
    week_start, _ = ist_next_days_range_utc(7)

    # client_a: session today, no check-in today -> pending.
    session_a = _make_session(
        client_a.id,
        trainer.id,
        scheduled_start=today_session_time,
        scheduled_end=today_session_time + timedelta(minutes=60),
        status=SessionStatus.SCHEDULED,
    )
    session_repository.seed(session_a)
    dashboard_repository.seed_session(session_a)

    # client_b: session today, check-in already submitted today -> not pending.
    session_b = _make_session(
        client_b.id,
        trainer.id,
        scheduled_start=today_session_time,
        scheduled_end=today_session_time + timedelta(minutes=60),
        status=SessionStatus.SCHEDULED,
    )
    session_repository.seed(session_b)
    dashboard_repository.seed_session(session_b)
    check_in_b = _make_check_in(client_b.id, uuid.uuid4(), submitted_at=today_session_time)
    check_in_repository.seed(check_in_b)
    dashboard_repository.seed_check_in(check_in_b)

    # client_a: a future session later this week (not today) -> only counted
    # in the 7-day window, not in sessions_today.
    future_time = week_start + timedelta(days=3)
    session_future = _make_session(
        client_a.id,
        trainer.id,
        scheduled_start=future_time,
        scheduled_end=future_time + timedelta(minutes=60),
        status=SessionStatus.SCHEDULED,
    )
    session_repository.seed(session_future)

    application_setting_service = _application_setting_service(
        measurement_overdue_days=14, subscription_expired_days=30
    )

    return {
        "dashboard_repository": dashboard_repository,
        "client_repository": client_repository,
        "assignment_repository": assignment_repository,
        "session_repository": session_repository,
        "check_in_repository": check_in_repository,
        "measurement_repository": measurement_repository,
        "subscription_repository": subscription_repository,
        "application_setting_service": application_setting_service,
        "trainer_user_id": trainer_user_id,
    }


def test_trainer_dashboard_computes_all_fields():
    fixture = _build_shared_fixture()
    service = _make_service(**{k: v for k, v in fixture.items() if k != "trainer_user_id"})

    dashboard = asyncio.run(
        service.get_trainer_dashboard(
            actor_role=RoleName.TRAINER, actor_id=fixture["trainer_user_id"]
        )
    )

    assert dashboard.assigned_clients == 2
    assert dashboard.active_clients == 1
    assert dashboard.sessions_today == 2
    assert dashboard.upcoming_sessions_next_7_days == 3
    assert dashboard.pending_check_ins == 1
    assert dashboard.pending_measurements == 1


def test_super_admin_dashboard_computes_all_fields():
    fixture = _build_shared_fixture()
    service = _make_service(**{k: v for k, v in fixture.items() if k != "trainer_user_id"})

    dashboard = asyncio.run(service.get_super_admin_dashboard(actor_role=RoleName.SUPER_ADMIN))

    assert dashboard.total_clients == 2
    assert dashboard.active_clients == 1
    assert dashboard.expired_clients == 1
    assert dashboard.inactive_clients == 0
    assert dashboard.total_trainers == 1
    assert dashboard.sessions_today == 2
    assert dashboard.upcoming_sessions_next_7_days == 3
    assert dashboard.measurements_recorded_this_month == 1
    assert dashboard.check_ins_submitted_today == 1
    assert dashboard.clients_missing_check_ins_today == 1


# ---------------------------------------------------------------------------
# Client dashboard
# ---------------------------------------------------------------------------


def _build_client_fixture(*, sessions_per_week: int | None = 3):
    client_repository = FakeClientRepository()
    session_repository = FakeSessionRepository()
    check_in_repository = FakeCheckInRepository()
    subscription_repository = FakeSubscriptionRepository()

    user_id = uuid.uuid4()
    client = _make_client(user_id, timezone="Asia/Kolkata")
    client_repository.seed(client, "client@example.com")

    trainer_id = uuid.uuid4()
    plan = _make_plan(sessions_per_week=sessions_per_week)

    if sessions_per_week is not None:
        today = current_india_date()
        subscription_repository.seed(
            _make_subscription(
                client.id,
                plan.id,
                start_date=today - timedelta(days=10),
                end_date=today + timedelta(days=20),
                plan_sessions_per_week=sessions_per_week,
            )
        )

    return {
        "client_repository": client_repository,
        "session_repository": session_repository,
        "check_in_repository": check_in_repository,
        "subscription_repository": subscription_repository,
        "client": client,
        "trainer_id": trainer_id,
        "user_id": user_id,
    }


def test_client_dashboard_target_check_ins_from_latest_subscription():
    fixture = _build_client_fixture(sessions_per_week=4)
    service = _make_service(
        client_repository=fixture["client_repository"],
        session_repository=fixture["session_repository"],
        check_in_repository=fixture["check_in_repository"],
        subscription_repository=fixture["subscription_repository"],
    )

    dashboard = asyncio.run(
        service.get_client_dashboard(actor_role=RoleName.CLIENT, actor_id=fixture["user_id"])
    )

    assert dashboard.target_check_ins == 4


def test_client_dashboard_target_check_ins_none_without_subscription():
    fixture = _build_client_fixture(sessions_per_week=None)
    service = _make_service(
        client_repository=fixture["client_repository"],
        session_repository=fixture["session_repository"],
        check_in_repository=fixture["check_in_repository"],
        subscription_repository=fixture["subscription_repository"],
    )

    dashboard = asyncio.run(
        service.get_client_dashboard(actor_role=RoleName.CLIENT, actor_id=fixture["user_id"])
    )

    assert dashboard.target_check_ins is None


def test_client_dashboard_check_ins_this_week():
    fixture = _build_client_fixture()
    client = fixture["client"]
    week_start, week_end = client_week_range_utc(client.timezone)
    in_week_time = _midpoint(week_start, week_end)

    fixture["check_in_repository"].seed(
        _make_check_in(client.id, uuid.uuid4(), submitted_at=in_week_time)
    )
    fixture["check_in_repository"].seed(
        _make_check_in(client.id, uuid.uuid4(), submitted_at=in_week_time + timedelta(minutes=1))
    )
    # Outside the week window - must not be counted.
    fixture["check_in_repository"].seed(
        _make_check_in(client.id, uuid.uuid4(), submitted_at=week_start - timedelta(days=10))
    )

    service = _make_service(
        client_repository=fixture["client_repository"],
        session_repository=fixture["session_repository"],
        check_in_repository=fixture["check_in_repository"],
        subscription_repository=fixture["subscription_repository"],
    )

    dashboard = asyncio.run(
        service.get_client_dashboard(actor_role=RoleName.CLIENT, actor_id=fixture["user_id"])
    )

    assert dashboard.check_ins_this_week == 2


def test_client_dashboard_adherence_percentage():
    fixture = _build_client_fixture()
    client = fixture["client"]
    window_start, window_end = client_last_n_days_range_utc(client.timezone, 90)
    in_window_time = _midpoint(window_start, window_end)

    # 4 non-cancelled sessions in the window (expected), 1 cancelled (excluded).
    for offset_minutes in range(4):
        fixture["session_repository"].seed(
            _make_session(
                client.id,
                fixture["trainer_id"],
                scheduled_start=in_window_time + timedelta(minutes=offset_minutes),
                scheduled_end=in_window_time + timedelta(minutes=offset_minutes + 60),
                status=SessionStatus.SCHEDULED,
            )
        )
    fixture["session_repository"].seed(
        _make_session(
            client.id,
            fixture["trainer_id"],
            scheduled_start=in_window_time + timedelta(minutes=100),
            scheduled_end=in_window_time + timedelta(minutes=160),
            status=SessionStatus.CANCELLED,
        )
    )

    # 3 check-ins submitted in the window.
    for offset_minutes in range(3):
        fixture["check_in_repository"].seed(
            _make_check_in(
                client.id, uuid.uuid4(), submitted_at=in_window_time + timedelta(minutes=offset_minutes)
            )
        )

    service = _make_service(
        client_repository=fixture["client_repository"],
        session_repository=fixture["session_repository"],
        check_in_repository=fixture["check_in_repository"],
        subscription_repository=fixture["subscription_repository"],
    )

    dashboard = asyncio.run(
        service.get_client_dashboard(actor_role=RoleName.CLIENT, actor_id=fixture["user_id"])
    )

    assert dashboard.check_in_adherence_percentage == 75


def test_client_dashboard_adherence_zero_when_no_expected_sessions():
    fixture = _build_client_fixture()
    service = _make_service(
        client_repository=fixture["client_repository"],
        session_repository=fixture["session_repository"],
        check_in_repository=fixture["check_in_repository"],
        subscription_repository=fixture["subscription_repository"],
    )

    dashboard = asyncio.run(
        service.get_client_dashboard(actor_role=RoleName.CLIENT, actor_id=fixture["user_id"])
    )

    assert dashboard.check_in_adherence_percentage == 0
