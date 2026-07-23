import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from core.constants import RoleName
from core.deps import CurrentUser, get_current_user
from main import app
from models.client_trainer_assignment import ClientTrainerAssignment
from models.session import SessionStatus
from models.subscription import SubscriptionStatus
from routers.sessions import (
    get_assignment_repository,
    get_client_repository,
    get_session_repository,
    get_subscription_plan_repository,
    get_subscription_repository,
)
from tests.services.test_assignment_service import FakeAssignmentRepository, _make_trainer
from tests.services.test_client_service import FakeClientRepository, _make_client
from tests.services.test_session_service import (
    FakeSessionRepository,
    _make_session,
    _setup_eligible_pair,
)
from tests.services.test_subscription_plan_service import (
    FakeSubscriptionPlanRepository,
    _make_plan,
)
from tests.services.test_subscription_service import FakeSubscriptionRepository, _make_subscription


def _make_repos() -> tuple[
    FakeSessionRepository,
    FakeClientRepository,
    FakeAssignmentRepository,
    FakeSubscriptionRepository,
    FakeSubscriptionPlanRepository,
]:
    return (
        FakeSessionRepository(),
        FakeClientRepository(),
        FakeAssignmentRepository(),
        FakeSubscriptionRepository(),
        FakeSubscriptionPlanRepository(),
    )


def _override_dependencies(
    session_repository: FakeSessionRepository,
    client_repository: FakeClientRepository,
    assignment_repository: FakeAssignmentRepository,
    subscription_repository: FakeSubscriptionRepository,
    subscription_plan_repository: FakeSubscriptionPlanRepository,
    user_id: uuid.UUID,
    active_role: str | None,
) -> None:
    app.dependency_overrides[get_session_repository] = lambda: session_repository
    app.dependency_overrides[get_client_repository] = lambda: client_repository
    app.dependency_overrides[get_assignment_repository] = lambda: assignment_repository
    app.dependency_overrides[get_subscription_repository] = lambda: subscription_repository
    app.dependency_overrides[get_subscription_plan_repository] = (
        lambda: subscription_plan_repository
    )
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=user_id, active_role=active_role
    )


def teardown_function() -> None:
    app.dependency_overrides.clear()


def _future_iso(days: int = 1) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def test_create_session_succeeds_for_super_admin():
    session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_repos()
    )
    client, trainer, _ = _setup_eligible_pair(
        client_repository, assignment_repository, subscription_repository, plan_repository
    )
    _override_dependencies(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/sessions",
        json={
            "client_id": str(client.id),
            "trainer_id": str(trainer.id),
            "scheduled_start": _future_iso(),
            "duration_minutes": 60,
            "meeting_type": "GOOGLE_MEET",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["client_id"] == str(client.id)
    assert body["trainer_id"] == str(trainer.id)
    assert body["status"] == "SCHEDULED"


def test_create_session_rejects_client_role():
    session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_repos()
    )
    _override_dependencies(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        uuid.uuid4(),
        RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/sessions",
        json={
            "client_id": str(uuid.uuid4()),
            "trainer_id": str(uuid.uuid4()),
            "scheduled_start": _future_iso(),
            "meeting_type": "GOOGLE_MEET",
        },
    )

    assert response.status_code == 403


def test_create_session_requires_authentication():
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/sessions",
        json={
            "client_id": str(uuid.uuid4()),
            "trainer_id": str(uuid.uuid4()),
            "scheduled_start": _future_iso(),
            "meeting_type": "GOOGLE_MEET",
        },
    )

    assert response.status_code == 401


def test_create_session_rejects_naive_datetime():
    session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_repos()
    )
    client, trainer, _ = _setup_eligible_pair(
        client_repository, assignment_repository, subscription_repository, plan_repository
    )
    _override_dependencies(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/sessions",
        json={
            "client_id": str(client.id),
            "trainer_id": str(trainer.id),
            "scheduled_start": "2026-08-10T19:00:00",
            "meeting_type": "GOOGLE_MEET",
        },
    )

    assert response.status_code == 422


def test_create_session_returns_400_for_past_session():
    session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_repos()
    )
    client, trainer, _ = _setup_eligible_pair(
        client_repository, assignment_repository, subscription_repository, plan_repository
    )
    _override_dependencies(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/sessions",
        json={
            "client_id": str(client.id),
            "trainer_id": str(trainer.id),
            "scheduled_start": _future_iso(days=-1),
            "meeting_type": "GOOGLE_MEET",
        },
    )

    assert response.status_code == 400


def test_create_session_returns_409_for_session_limit_reached():
    session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_repos()
    )
    client, trainer, _ = _setup_eligible_pair(
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        max_sessions_per_month=1,
    )
    existing_start = datetime.now(timezone.utc) + timedelta(days=10)
    session_repository.seed(
        _make_session(
            client.id,
            trainer.id,
            status=SessionStatus.COMPLETED,
            scheduled_start=existing_start,
            scheduled_end=existing_start + timedelta(hours=1),
        )
    )
    _override_dependencies(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/sessions",
        json={
            "client_id": str(client.id),
            "trainer_id": str(trainer.id),
            "scheduled_start": _future_iso(),
            "meeting_type": "GOOGLE_MEET",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Client has reached the maximum number of sessions for this subscription."
    }


def test_create_session_returns_403_for_unassigned_trainer():
    session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_repos()
    )
    client = _make_client(user_id=uuid.uuid4())
    trainer = _make_trainer(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    assignment_repository.seed_trainer(trainer)
    _override_dependencies(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/sessions",
        json={
            "client_id": str(client.id),
            "trainer_id": str(trainer.id),
            "scheduled_start": _future_iso(),
            "meeting_type": "GOOGLE_MEET",
        },
    )

    assert response.status_code == 403


def test_bulk_create_sessions_succeeds_for_trainer():
    session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_repos()
    )
    client, trainer, trainer_user_id = _setup_eligible_pair(
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        max_sessions_per_month=12,
    )
    _override_dependencies(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        trainer_user_id,
        RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/sessions/bulk",
        json={
            "client_id": str(client.id),
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
            "days": ["MONDAY", "WEDNESDAY", "FRIDAY"],
            "start_time": "19:00",
            "duration_minutes": 60,
            "meeting_type": "GOOGLE_MEET",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["sessions_created"] == 12
    assert body["sessions_skipped"] == 1
    assert len(body["skipped_reasons"]) == 1


def test_bulk_create_sessions_rejects_client_role():
    session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_repos()
    )
    _override_dependencies(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        uuid.uuid4(),
        RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/sessions/bulk",
        json={
            "client_id": str(uuid.uuid4()),
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
            "days": ["MONDAY"],
            "start_time": "19:00",
            "duration_minutes": 60,
            "meeting_type": "GOOGLE_MEET",
        },
    )

    assert response.status_code == 403


def test_list_sessions_succeeds_for_super_admin():
    session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_repos()
    )
    for _ in range(3):
        session_repository.seed(_make_session(uuid.uuid4(), uuid.uuid4()))
    _override_dependencies(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/sessions?page=1&page_size=2")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2


def test_get_my_sessions_succeeds_for_client():
    session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_repos()
    )
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    client_repository.seed(client, "client@example.com")
    session_repository.seed(_make_session(client.id, uuid.uuid4()))
    _override_dependencies(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        client_user_id,
        RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/sessions/my-sessions")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["client_id"] == str(client.id)


def test_get_my_sessions_rejects_trainer_role():
    session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_repos()
    )
    _override_dependencies(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        uuid.uuid4(),
        RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/sessions/my-sessions")

    assert response.status_code == 403


def test_get_session_succeeds_for_super_admin():
    session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_repos()
    )
    session = _make_session(uuid.uuid4(), uuid.uuid4())
    session_repository.seed(session)
    _override_dependencies(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/sessions/{session.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(session.id)


def test_get_session_returns_404_for_missing_session():
    session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_repos()
    )
    _override_dependencies(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/sessions/{uuid.uuid4()}")

    assert response.status_code == 404


def test_get_session_rejects_unassigned_trainer():
    session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_repos()
    )
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    session = _make_session(uuid.uuid4(), uuid.uuid4())
    session_repository.seed(session)
    _override_dependencies(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        trainer_user_id,
        RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/sessions/{session.id}")

    assert response.status_code == 403


def test_update_session_succeeds_for_super_admin():
    session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_repos()
    )
    session = _make_session(uuid.uuid4(), uuid.uuid4())
    session_repository.seed(session)
    _override_dependencies(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.patch(
        f"/api/v1/sessions/{session.id}",
        json={"status": "COMPLETED", "trainer_notes": "Great progress."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["trainer_notes"] == "Great progress."


def test_update_session_rejects_client_role():
    session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_repos()
    )
    session = _make_session(uuid.uuid4(), uuid.uuid4())
    session_repository.seed(session)
    _override_dependencies(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        uuid.uuid4(),
        RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.patch(
        f"/api/v1/sessions/{session.id}", json={"status": "CANCELLED"}
    )

    assert response.status_code == 403


def test_update_session_returns_404_for_missing_session():
    session_repository, client_repository, assignment_repository, subscription_repository, plan_repository = (
        _make_repos()
    )
    _override_dependencies(
        session_repository,
        client_repository,
        assignment_repository,
        subscription_repository,
        plan_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.patch(
        f"/api/v1/sessions/{uuid.uuid4()}", json={"status": "CANCELLED"}
    )

    assert response.status_code == 404
