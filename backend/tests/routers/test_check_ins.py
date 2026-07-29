import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from core.constants import RoleName
from core.deps import CurrentUser, get_current_user
from main import app
from models.application_setting import ApplicationSetting
from models.client_trainer_assignment import ClientTrainerAssignment
from models.session import SessionStatus
from repositories.check_in_repository import PendingCheckInRow
from routers.check_ins import (
    get_application_setting_repository,
    get_assignment_repository,
    get_check_in_repository,
    get_client_repository,
    get_session_repository,
)
from tests.services.test_application_setting_service import FakeApplicationSettingRepository
from tests.services.test_assignment_service import FakeAssignmentRepository, _make_trainer
from tests.services.test_check_in_service import FakeCheckInRepository, _make_check_in
from tests.services.test_client_service import FakeClientRepository, _make_client
from tests.services.test_session_service import FakeSessionRepository, _make_session


def _make_repos() -> tuple[
    FakeCheckInRepository,
    FakeClientRepository,
    FakeAssignmentRepository,
    FakeSessionRepository,
    FakeApplicationSettingRepository,
]:
    application_setting_repository = FakeApplicationSettingRepository()
    application_setting_repository.seed(
        ApplicationSetting(
            id=uuid.uuid4(),
            key="check_in_edit_window_days",
            value="30",
            description="Edit window",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )
    return (
        FakeCheckInRepository(),
        FakeClientRepository(),
        FakeAssignmentRepository(),
        FakeSessionRepository(),
        application_setting_repository,
    )


def _override_dependencies(
    check_in_repository: FakeCheckInRepository,
    client_repository: FakeClientRepository,
    assignment_repository: FakeAssignmentRepository,
    session_repository: FakeSessionRepository,
    application_setting_repository: FakeApplicationSettingRepository,
    user_id: uuid.UUID,
    active_role: str | None,
) -> None:
    app.dependency_overrides[get_check_in_repository] = lambda: check_in_repository
    app.dependency_overrides[get_client_repository] = lambda: client_repository
    app.dependency_overrides[get_assignment_repository] = lambda: assignment_repository
    app.dependency_overrides[get_session_repository] = lambda: session_repository
    app.dependency_overrides[get_application_setting_repository] = (
        lambda: application_setting_repository
    )
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=user_id, active_role=active_role
    )


def teardown_function() -> None:
    app.dependency_overrides.clear()


def _setup_assigned_pair(client_repository, assignment_repository):
    client = _make_client(user_id=uuid.uuid4(), timezone="UTC")
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


def _past_session(session_repository, client_id, trainer_id, **overrides):
    started = datetime.now(timezone.utc) - timedelta(days=2)
    session = _make_session(
        client_id, trainer_id, scheduled_start=started, scheduled_end=started + timedelta(hours=1), **overrides
    )
    session_repository.seed(session)
    return session


# --- POST /api/v1/check-ins -----------------------------------------------------


def test_create_check_in_succeeds_for_super_admin():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins",
        json={"session_id": str(session.id), "sleep_hours": 7.5, "mood": 5},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["session_id"] == str(session.id)
    assert body["client_id"] == str(client.id)
    assert body["sleep_hours"] == 7.5
    assert body["mood"] == 5


def test_create_check_in_succeeds_for_assigned_trainer():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    client, trainer, trainer_user_id = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, trainer_user_id, RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins", json={"session_id": str(session.id), "energy_level": 4}
    )

    assert response.status_code == 201
    assert response.json()["submitted_by"] == str(trainer_user_id)


def test_create_check_in_succeeds_for_own_client():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id, timezone="UTC")
    client_repository.seed(client, "client@example.com")
    session = _past_session(session_repository, client.id, uuid.uuid4())
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, client_user_id, RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins",
        json={"session_id": str(session.id), "workout_completed": True, "diet_followed": False},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["submitted_by"] == str(client_user_id)
    assert body["workout_completed"] is True
    assert body["diet_followed"] is False


def test_create_check_in_rejects_client_submitting_for_another_clients_session():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id, timezone="UTC")
    other_client = _make_client(user_id=uuid.uuid4(), timezone="UTC")
    client_repository.seed(client, "client@example.com")
    client_repository.seed(other_client, "other@example.com")
    session = _past_session(session_repository, other_client.id, uuid.uuid4())
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, client_user_id, RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins", json={"session_id": str(session.id), "mood": 3}
    )

    assert response.status_code == 403


def test_create_check_in_rejects_unassigned_trainer():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    client = _make_client(user_id=uuid.uuid4(), timezone="UTC")
    client_repository.seed(client, "client@example.com")
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    session = _past_session(session_repository, client.id, uuid.uuid4())
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, trainer_user_id, RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins", json={"session_id": str(session.id), "mood": 3}
    )

    assert response.status_code == 403


def test_create_check_in_requires_authentication():
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins", json={"session_id": str(uuid.uuid4()), "mood": 3}
    )

    assert response.status_code == 401


def test_create_check_in_rejects_empty_payload():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post("/api/v1/check-ins", json={"session_id": str(session.id)})

    assert response.status_code == 400
    assert response.json() == {"detail": "At least one check-in field must be provided."}


def test_create_check_in_returns_404_for_missing_session():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins", json={"session_id": str(uuid.uuid4()), "mood": 3}
    )

    assert response.status_code == 404


def test_create_check_in_rejects_cancelled_session():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id, status=SessionStatus.CANCELLED)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins", json={"session_id": str(session.id), "mood": 3}
    )

    assert response.status_code == 409


def test_create_check_in_rejects_session_not_yet_started():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    future_start = datetime.now(timezone.utc) + timedelta(days=1)
    session = _make_session(
        client.id, trainer.id, scheduled_start=future_start, scheduled_end=future_start + timedelta(hours=1)
    )
    session_repository.seed(session)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins", json={"session_id": str(session.id), "mood": 3}
    )

    assert response.status_code == 409


def test_create_check_in_prevents_duplicate_for_session():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    first = test_client.post(
        "/api/v1/check-ins", json={"session_id": str(session.id), "mood": 3}
    )
    assert first.status_code == 201

    second = test_client.post(
        "/api/v1/check-ins", json={"session_id": str(session.id), "mood": 5}
    )

    assert second.status_code == 409


def test_create_check_in_rejects_mood_out_of_range():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins", json={"session_id": str(session.id), "mood": 6}
    )

    assert response.status_code == 422


# --- PATCH /api/v1/check-ins/{id} -----------------------------------------------


def test_update_check_in_succeeds_within_edit_window():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id)
    check_in = _make_check_in(session.id, client.id, trainer.id, mood=3)
    check_in_repository.seed(check_in)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.patch(f"/api/v1/check-ins/{check_in.id}", json={"mood": 5})

    assert response.status_code == 200
    assert response.json()["mood"] == 5


def test_update_check_in_rejects_after_edit_window_expired():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    setting_repository.seed(
        ApplicationSetting(
            id=uuid.uuid4(),
            key="check_in_edit_window_days",
            value="1",
            description="Edit window",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    started = datetime.now(timezone.utc) - timedelta(days=5)
    session = _make_session(
        client.id, trainer.id, scheduled_start=started, scheduled_end=started + timedelta(hours=1)
    )
    session_repository.seed(session)
    check_in = _make_check_in(session.id, client.id, trainer.id, mood=3)
    check_in_repository.seed(check_in)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.patch(f"/api/v1/check-ins/{check_in.id}", json={"mood": 5})

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "This check-in can no longer be modified. The configured edit window "
            "has expired."
        )
    }


def test_update_check_in_returns_404_for_missing_check_in():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.patch(f"/api/v1/check-ins/{uuid.uuid4()}", json={"mood": 5})

    assert response.status_code == 404


# --- GET /api/v1/check-ins/session/{id} -----------------------------------------


def test_get_check_in_by_session_succeeds():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id)
    check_in_repository.seed(_make_check_in(session.id, client.id, trainer.id, mood=4))
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/check-ins/session/{session.id}")

    assert response.status_code == 200
    assert response.json()["mood"] == 4


def test_get_check_in_by_session_returns_404_without_check_in():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/check-ins/session/{session.id}")

    assert response.status_code == 404


# --- GET /api/v1/check-ins/client/{id} (client can view own) -------------------


def test_client_can_view_own_check_ins():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id, timezone="UTC")
    client_repository.seed(client, "client@example.com")
    check_in_repository.seed(_make_check_in(uuid.uuid4(), client.id, uuid.uuid4()))
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, client_user_id, RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/check-ins/client/{client.id}")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["client_id"] == str(client.id)


def test_client_cannot_view_other_clients_check_ins():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id, timezone="UTC")
    other_client = _make_client(user_id=uuid.uuid4(), timezone="UTC")
    client_repository.seed(client, "client@example.com")
    client_repository.seed(other_client, "other@example.com")
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, client_user_id, RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/check-ins/client/{other_client.id}")

    assert response.status_code == 403


def test_get_client_check_ins_returns_404_for_missing_client():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/check-ins/client/{uuid.uuid4()}")

    assert response.status_code == 404


# --- GET /api/v1/check-ins/pending ----------------------------------------------


def test_pending_check_ins_allowed_for_trainer():
    # FakeCheckInRepository.list_pending returns manually seeded rows rather
    # than re-deriving the Session/CheckIn join (that join is exercised by
    # the real SQLAlchemy repository against Postgres, not the in-memory
    # fake) - this seeded row simulates what that join would produce.
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    client, trainer, trainer_user_id = _setup_assigned_pair(client_repository, assignment_repository)
    session = _past_session(session_repository, client.id, trainer.id)
    check_in_repository.seed_pending_row(
        PendingCheckInRow(
            session_id=session.id,
            client_id=client.id,
            client_name=f"{client.first_name} {client.last_name}",
            scheduled_start=session.scheduled_start,
        )
    )
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, trainer_user_id, RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/check-ins/pending")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["session_id"] == str(session.id)
    assert body[0]["client_id"] == str(client.id)


def test_pending_check_ins_returns_empty_list_when_none_pending():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    _, _, trainer_user_id = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, trainer_user_id, RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/check-ins/pending")

    assert response.status_code == 200
    assert response.json() == []


def test_pending_check_ins_rejects_client_role():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, uuid.uuid4(), RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/check-ins/pending")

    assert response.status_code == 403


# --- GET /api/v1/check-ins/{id} -------------------------------------------------


def test_get_check_in_by_id_succeeds_for_super_admin():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    check_in = _make_check_in(uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
    check_in_repository.seed(check_in)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/check-ins/{check_in.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(check_in.id)


def test_get_check_in_by_id_returns_404_for_missing_check_in():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/check-ins/{uuid.uuid4()}")

    assert response.status_code == 404


# --- GET /api/v1/check-ins (paginated list) -------------------------------------


def test_list_check_ins_succeeds_for_super_admin():
    check_in_repository, client_repository, assignment_repository, session_repository, setting_repository = (
        _make_repos()
    )
    for _ in range(3):
        check_in_repository.seed(_make_check_in(uuid.uuid4(), uuid.uuid4(), uuid.uuid4()))
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository, session_repository,
        setting_repository, uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/check-ins?page=1&page_size=2")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2


# --- Existing functionality remains unaffected ----------------------------------


def test_existing_measurements_endpoint_unaffected_by_check_ins_module():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/measurements")

    # Unauthenticated request still behaves exactly as before (401), proving
    # the measurements router/module was not disturbed by adding check-ins.
    assert response.status_code == 401


def test_existing_sessions_endpoint_unaffected_by_check_ins_module():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/sessions")

    assert response.status_code == 401


def test_health_endpoint_unaffected():
    test_client = TestClient(app)

    response = test_client.get("/health")

    assert response.status_code == 200
