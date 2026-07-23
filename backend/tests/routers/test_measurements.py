import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from core.constants import RoleName
from core.deps import CurrentUser, get_current_user
from main import app
from models.client_trainer_assignment import ClientTrainerAssignment
from routers.measurements import (
    get_assignment_repository,
    get_client_repository,
    get_measurement_repository,
)
from tests.services.test_assignment_service import FakeAssignmentRepository, _make_trainer
from tests.services.test_client_service import FakeClientRepository, _make_client
from tests.services.test_measurement_service import FakeMeasurementRepository, _make_measurement


def _make_repos() -> tuple[FakeMeasurementRepository, FakeClientRepository, FakeAssignmentRepository]:
    return FakeMeasurementRepository(), FakeClientRepository(), FakeAssignmentRepository()


def _override_dependencies(
    measurement_repository: FakeMeasurementRepository,
    client_repository: FakeClientRepository,
    assignment_repository: FakeAssignmentRepository,
    user_id: uuid.UUID,
    active_role: str | None,
) -> None:
    app.dependency_overrides[get_measurement_repository] = lambda: measurement_repository
    app.dependency_overrides[get_client_repository] = lambda: client_repository
    app.dependency_overrides[get_assignment_repository] = lambda: assignment_repository
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=user_id, active_role=active_role
    )


def teardown_function() -> None:
    app.dependency_overrides.clear()


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


# --- POST /api/v1/measurements ------------------------------------------------


def test_create_measurement_with_weight_only_succeeds_for_super_admin():
    measurement_repository, client_repository, assignment_repository = _make_repos()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        measurement_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/measurements", json={"client_id": str(client.id), "weight_kg": 80}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["client_id"] == str(client.id)
    assert body["weight_kg"] == 80
    assert body["body_fat_percentage"] is None


def test_create_measurement_with_multiple_fields_succeeds():
    measurement_repository, client_repository, assignment_repository = _make_repos()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        measurement_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/measurements",
        json={
            "client_id": str(client.id),
            "weight_kg": 80,
            "body_fat_percentage": 18,
            "waist_cm": 92,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["weight_kg"] == 80
    assert body["body_fat_percentage"] == 18
    assert body["waist_cm"] == 92


def test_create_measurement_rejects_empty_payload():
    measurement_repository, client_repository, assignment_repository = _make_repos()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        measurement_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/measurements", json={"client_id": str(client.id)}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "At least one measurement field must be provided."}


def test_create_measurement_succeeds_for_assigned_trainer():
    measurement_repository, client_repository, assignment_repository = _make_repos()
    client, trainer, trainer_user_id = _setup_assigned_pair(
        client_repository, assignment_repository
    )
    _override_dependencies(
        measurement_repository, client_repository, assignment_repository,
        trainer_user_id, RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/measurements", json={"client_id": str(client.id), "weight_kg": 78}
    )

    assert response.status_code == 201
    assert response.json()["recorded_by"] == str(trainer_user_id)


def test_create_measurement_rejects_unassigned_trainer():
    measurement_repository, client_repository, assignment_repository = _make_repos()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    _override_dependencies(
        measurement_repository, client_repository, assignment_repository,
        trainer_user_id, RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/measurements", json={"client_id": str(client.id), "weight_kg": 78}
    )

    assert response.status_code == 403


def test_create_measurement_rejects_client_role():
    measurement_repository, client_repository, assignment_repository = _make_repos()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        measurement_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/measurements", json={"client_id": str(client.id), "weight_kg": 78}
    )

    assert response.status_code == 403


def test_create_measurement_requires_authentication():
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/measurements", json={"client_id": str(uuid.uuid4()), "weight_kg": 78}
    )

    assert response.status_code == 401


def test_create_measurement_rejects_naive_recorded_at():
    measurement_repository, client_repository, assignment_repository = _make_repos()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        measurement_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/measurements",
        json={
            "client_id": str(client.id),
            "weight_kg": 78,
            "recorded_at": "2026-08-10T19:00:00",
        },
    )

    assert response.status_code == 422


# --- GET /api/v1/measurements/client/{id} (client can view own) --------------


def test_client_can_view_own_measurements():
    measurement_repository, client_repository, assignment_repository = _make_repos()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    client_repository.seed(client, "client@example.com")
    measurement_repository.seed(_make_measurement(client.id, uuid.uuid4()))
    _override_dependencies(
        measurement_repository, client_repository, assignment_repository,
        client_user_id, RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/measurements/client/{client.id}")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["client_id"] == str(client.id)


def test_client_cannot_view_other_clients_measurements():
    measurement_repository, client_repository, assignment_repository = _make_repos()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    client_repository.seed(other_client, "other@example.com")
    _override_dependencies(
        measurement_repository, client_repository, assignment_repository,
        client_user_id, RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/measurements/client/{other_client.id}")

    assert response.status_code == 403


def test_get_client_measurements_returns_404_for_missing_client():
    measurement_repository, client_repository, assignment_repository = _make_repos()
    _override_dependencies(
        measurement_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/measurements/client/{uuid.uuid4()}")

    assert response.status_code == 404


# --- GET /api/v1/measurements/client/{id}/latest ------------------------------


def test_latest_endpoint_computes_change_from_previous():
    measurement_repository, client_repository, assignment_repository = _make_repos()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    now = datetime.now(timezone.utc)
    measurement_repository.seed(
        _make_measurement(
            client.id, trainer.id, weight_kg=82, waist_cm=94, recorded_at=now - timedelta(days=14)
        )
    )
    measurement_repository.seed(
        _make_measurement(client.id, trainer.id, weight_kg=80, waist_cm=92, recorded_at=now)
    )
    _override_dependencies(
        measurement_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/measurements/client/{client.id}/latest")

    assert response.status_code == 200
    body = response.json()
    assert body["weight_kg"] == 80
    assert body["previous_weight_kg"] == 82
    assert body["weight_change"] == -2
    assert body["waist_cm"] == 92
    assert body["previous_waist_cm"] == 94
    assert body["waist_change"] == -2


def test_latest_endpoint_returns_null_change_without_previous():
    measurement_repository, client_repository, assignment_repository = _make_repos()
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    measurement_repository.seed(_make_measurement(client.id, trainer.id, weight_kg=80))
    _override_dependencies(
        measurement_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/measurements/client/{client.id}/latest")

    assert response.status_code == 200
    body = response.json()
    assert body["weight_kg"] == 80
    assert body["previous_weight_kg"] is None
    assert body["weight_change"] is None


def test_latest_endpoint_returns_404_without_any_measurements():
    measurement_repository, client_repository, assignment_repository = _make_repos()
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        measurement_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/measurements/client/{client.id}/latest")

    assert response.status_code == 404


# --- GET /api/v1/measurements/{id} --------------------------------------------


def test_get_measurement_by_id_succeeds_for_super_admin():
    measurement_repository, client_repository, assignment_repository = _make_repos()
    measurement = _make_measurement(uuid.uuid4(), uuid.uuid4())
    measurement_repository.seed(measurement)
    _override_dependencies(
        measurement_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/measurements/{measurement.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(measurement.id)


def test_get_measurement_by_id_returns_404_for_missing_measurement():
    measurement_repository, client_repository, assignment_repository = _make_repos()
    _override_dependencies(
        measurement_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/measurements/{uuid.uuid4()}")

    assert response.status_code == 404


# --- GET /api/v1/measurements (paginated list) --------------------------------


def test_list_measurements_succeeds_for_super_admin():
    measurement_repository, client_repository, assignment_repository = _make_repos()
    for _ in range(3):
        measurement_repository.seed(_make_measurement(uuid.uuid4(), uuid.uuid4()))
    _override_dependencies(
        measurement_repository, client_repository, assignment_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/measurements?page=1&page_size=2")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2


# --- Existing functionality remains unaffected --------------------------------


def test_existing_sessions_endpoint_unaffected_by_measurements_module():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/sessions")

    # Unauthenticated request still behaves exactly as before (401), proving
    # the sessions router/module was not disturbed by adding measurements.
    assert response.status_code == 401


def test_health_endpoint_unaffected():
    test_client = TestClient(app)

    response = test_client.get("/health")

    assert response.status_code == 200
