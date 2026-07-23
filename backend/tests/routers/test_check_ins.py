import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from core.constants import RoleName
from core.deps import CurrentUser, get_current_user
from main import app
from models.client_trainer_assignment import ClientTrainerAssignment
from routers.check_ins import (
    get_assignment_repository,
    get_check_in_repository,
    get_client_repository,
)
from tests.services.test_assignment_service import FakeAssignmentRepository, _make_trainer
from tests.services.test_check_in_service import FakeCheckInRepository, _make_check_in
from tests.services.test_client_service import FakeClientRepository, _make_client


def _make_repos() -> tuple[FakeCheckInRepository, FakeClientRepository, FakeAssignmentRepository]:
    return FakeCheckInRepository(), FakeClientRepository(), FakeAssignmentRepository()


def _override_dependencies(
    check_in_repository: FakeCheckInRepository,
    client_repository: FakeClientRepository,
    assignment_repository: FakeAssignmentRepository,
    user_id: uuid.UUID,
    active_role: str | None,
) -> None:
    app.dependency_overrides[get_check_in_repository] = lambda: check_in_repository
    app.dependency_overrides[get_client_repository] = lambda: client_repository
    app.dependency_overrides[get_assignment_repository] = lambda: assignment_repository
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


# --- POST /api/v1/check-ins -----------------------------------------------------


def test_create_check_in_succeeds_for_super_admin():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins",
        json={"client_id": str(client.id), "sleep_hours": 7.5, "mood": 5},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["client_id"] == str(client.id)
    assert body["sleep_hours"] == 7.5
    assert body["mood"] == 5


def test_create_check_in_succeeds_for_assigned_trainer():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    client, trainer, trainer_user_id = _setup_assigned_pair(
        client_repository, assignment_repository
    )
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        trainer_user_id, RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins", json={"client_id": str(client.id), "energy_level": 4}
    )

    assert response.status_code == 201
    assert response.json()["submitted_by"] == str(trainer_user_id)


def test_create_check_in_succeeds_for_own_client():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id, timezone="UTC")
    client_repository.seed(client, "client@example.com")
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        client_user_id, RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins",
        json={"client_id": str(client.id), "workout_completed": True, "diet_followed": False},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["submitted_by"] == str(client_user_id)
    assert body["workout_completed"] is True
    assert body["diet_followed"] is False


def test_create_check_in_rejects_client_submitting_for_another_client():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id, timezone="UTC")
    other_client = _make_client(user_id=uuid.uuid4(), timezone="UTC")
    client_repository.seed(client, "client@example.com")
    client_repository.seed(other_client, "other@example.com")
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        client_user_id, RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins", json={"client_id": str(other_client.id), "mood": 3}
    )

    assert response.status_code == 403


def test_create_check_in_rejects_unassigned_trainer():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    client = _make_client(user_id=uuid.uuid4(), timezone="UTC")
    client_repository.seed(client, "client@example.com")
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        trainer_user_id, RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins", json={"client_id": str(client.id), "mood": 3}
    )

    assert response.status_code == 403


def test_create_check_in_requires_authentication():
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins", json={"client_id": str(uuid.uuid4()), "mood": 3}
    )

    assert response.status_code == 401


def test_create_check_in_rejects_empty_payload():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post("/api/v1/check-ins", json={"client_id": str(client.id)})

    assert response.status_code == 400
    assert response.json() == {"detail": "At least one check-in field must be provided."}


def test_create_check_in_prevents_duplicate_for_same_day():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)
    today_noon = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)

    first = test_client.post(
        "/api/v1/check-ins",
        json={
            "client_id": str(client.id),
            "mood": 3,
            "submitted_at": today_noon.isoformat(),
        },
    )
    assert first.status_code == 201

    second = test_client.post(
        "/api/v1/check-ins",
        json={
            "client_id": str(client.id),
            "mood": 5,
            "submitted_at": (today_noon + timedelta(hours=2)).isoformat(),
        },
    )

    assert second.status_code == 409
    assert second.json() == {"detail": "Check-in already exists for this date."}


def test_create_check_in_rejects_mood_out_of_range():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins", json={"client_id": str(client.id), "mood": 6}
    )

    assert response.status_code == 422


def test_create_check_in_rejects_energy_level_out_of_range():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins", json={"client_id": str(client.id), "energy_level": 0}
    )

    assert response.status_code == 422


def test_create_check_in_rejects_naive_submitted_at():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/check-ins",
        json={
            "client_id": str(client.id),
            "mood": 3,
            "submitted_at": "2026-08-10T19:00:00",
        },
    )

    assert response.status_code == 422


# --- GET /api/v1/check-ins/client/{id} (client can view own) -------------------


def test_client_can_view_own_check_ins():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id, timezone="UTC")
    client_repository.seed(client, "client@example.com")
    check_in_repository.seed(_make_check_in(client.id, uuid.uuid4()))
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        client_user_id, RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/check-ins/client/{client.id}")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["client_id"] == str(client.id)


def test_client_cannot_view_other_clients_check_ins():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id, timezone="UTC")
    other_client = _make_client(user_id=uuid.uuid4(), timezone="UTC")
    client_repository.seed(client, "client@example.com")
    client_repository.seed(other_client, "other@example.com")
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        client_user_id, RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/check-ins/client/{other_client.id}")

    assert response.status_code == 403


def test_trainer_cannot_view_unassigned_clients_check_ins():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    client = _make_client(user_id=uuid.uuid4(), timezone="UTC")
    client_repository.seed(client, "client@example.com")
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        trainer_user_id, RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/check-ins/client/{client.id}")

    assert response.status_code == 403


def test_trainer_can_view_assigned_clients_check_ins():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    client, trainer, trainer_user_id = _setup_assigned_pair(
        client_repository, assignment_repository
    )
    check_in_repository.seed(_make_check_in(client.id, trainer.id))
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        trainer_user_id, RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/check-ins/client/{client.id}")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_client_check_ins_returns_404_for_missing_client():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/check-ins/client/{uuid.uuid4()}")

    assert response.status_code == 404


# --- GET /api/v1/check-ins/client/{id}/latest -----------------------------------


def test_latest_endpoint_returns_most_recent_check_in():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    now = datetime.now(timezone.utc)
    check_in_repository.seed(
        _make_check_in(client.id, trainer.id, mood=3, submitted_at=now - timedelta(days=1))
    )
    check_in_repository.seed(
        _make_check_in(
            client.id,
            trainer.id,
            sleep_hours=7.5,
            water_intake_liters=3,
            energy_level=4,
            mood=5,
            workout_completed=True,
            diet_followed=True,
            submitted_at=now,
        )
    )
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/check-ins/client/{client.id}/latest")

    assert response.status_code == 200
    body = response.json()
    assert body["sleep_hours"] == 7.5
    assert body["water_intake_liters"] == 3
    assert body["energy_level"] == 4
    assert body["mood"] == 5
    assert body["workout_completed"] is True
    assert body["diet_followed"] is True
    assert "notes" not in body


def test_latest_endpoint_returns_404_without_any_check_ins():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/check-ins/client/{client.id}/latest")

    assert response.status_code == 404


# --- GET /api/v1/check-ins/{id} -------------------------------------------------


def test_get_check_in_by_id_succeeds_for_super_admin():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    check_in = _make_check_in(uuid.uuid4(), uuid.uuid4())
    check_in_repository.seed(check_in)
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/check-ins/{check_in.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(check_in.id)


def test_get_check_in_by_id_returns_404_for_missing_check_in():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/check-ins/{uuid.uuid4()}")

    assert response.status_code == 404


# --- GET /api/v1/check-ins (paginated list) -------------------------------------


def test_list_check_ins_succeeds_for_super_admin():
    check_in_repository, client_repository, assignment_repository = _make_repos()
    for _ in range(3):
        check_in_repository.seed(_make_check_in(uuid.uuid4(), uuid.uuid4()))
    _override_dependencies(
        check_in_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
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
