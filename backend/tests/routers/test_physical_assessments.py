import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from core.constants import RoleName
from core.deps import CurrentUser, get_current_user
from main import app
from models.application_setting import ApplicationSetting
from models.client_trainer_assignment import ClientTrainerAssignment
from repositories.physical_assessment_repository import LatestPhysicalAssessmentRow
from routers.physical_assessments import (
    get_application_setting_repository,
    get_assignment_repository,
    get_client_repository,
    get_physical_assessment_repository,
)
from tests.services.test_application_setting_service import FakeApplicationSettingRepository
from tests.services.test_assignment_service import FakeAssignmentRepository, _make_trainer
from tests.services.test_client_service import FakeClientRepository, _make_client
from tests.services.test_physical_assessment_service import FakePhysicalAssessmentRepository, _make_physical_assessment


def _make_repos() -> tuple[
    FakePhysicalAssessmentRepository,
    FakeClientRepository,
    FakeAssignmentRepository,
    FakeApplicationSettingRepository,
]:
    application_setting_repository = FakeApplicationSettingRepository()
    now = datetime.now(timezone.utc)
    application_setting_repository.seed(
        ApplicationSetting(
            id=uuid.uuid4(),
            key="physical_assessment_overdue_days",
            value="14",
            description="Days after which physical_assessments are overdue.",
            created_at=now,
            updated_at=now,
        )
    )
    application_setting_repository.seed(
        ApplicationSetting(
            id=uuid.uuid4(),
            key="physical_assessment_edit_window_days",
            value="30",
            description="Edit window",
            created_at=now,
            updated_at=now,
        )
    )
    return (
        FakePhysicalAssessmentRepository(),
        FakeClientRepository(),
        FakeAssignmentRepository(),
        application_setting_repository,
    )


def _override_dependencies(
    physical_assessment_repository: FakePhysicalAssessmentRepository,
    client_repository: FakeClientRepository,
    assignment_repository: FakeAssignmentRepository,
    application_setting_repository: FakeApplicationSettingRepository,
    user_id: uuid.UUID,
    active_role: str | None,
) -> None:
    app.dependency_overrides[get_physical_assessment_repository] = lambda: physical_assessment_repository
    app.dependency_overrides[get_client_repository] = lambda: client_repository
    app.dependency_overrides[get_assignment_repository] = lambda: assignment_repository
    app.dependency_overrides[get_application_setting_repository] = (
        lambda: application_setting_repository
    )
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


# --- POST /api/v1/physical-assessments ------------------------------------------------


def test_create_physical_assessment_with_weight_only_succeeds_for_super_admin():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/physical-assessments", json={"client_id": str(client.id), "weight_kg": 80}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["client_id"] == str(client.id)
    assert body["weight_kg"] == 80
    assert body["body_fat_percentage"] is None


def test_create_physical_assessment_with_multiple_fields_succeeds():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/physical-assessments",
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


def test_create_physical_assessment_rejects_empty_payload():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/physical-assessments", json={"client_id": str(client.id)}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "At least one physical assessment field must be provided."}


def test_create_physical_assessment_succeeds_for_assigned_trainer():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    client, trainer, trainer_user_id = _setup_assigned_pair(
        client_repository, assignment_repository
    )
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        trainer_user_id, RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/physical-assessments", json={"client_id": str(client.id), "weight_kg": 78}
    )

    assert response.status_code == 201
    assert response.json()["recorded_by"] == str(trainer_user_id)


def test_create_physical_assessment_rejects_unassigned_trainer():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    assignment_repository.seed_trainer(trainer)
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        trainer_user_id, RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/physical-assessments", json={"client_id": str(client.id), "weight_kg": 78}
    )

    assert response.status_code == 403


def test_create_physical_assessment_rejects_client_role():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        uuid.uuid4(), RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/physical-assessments", json={"client_id": str(client.id), "weight_kg": 78}
    )

    assert response.status_code == 403


def test_create_physical_assessment_requires_authentication():
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/physical-assessments", json={"client_id": str(uuid.uuid4()), "weight_kg": 78}
    )

    assert response.status_code == 401


def test_create_physical_assessment_rejects_naive_recorded_at():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/physical-assessments",
        json={
            "client_id": str(client.id),
            "weight_kg": 78,
            "recorded_at": "2026-08-10T19:00:00",
        },
    )

    assert response.status_code == 422


# --- GET /api/v1/physical-assessments/client/{id} (client can view own) --------------


def test_client_can_view_own_physical_assessments():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    client_repository.seed(client, "client@example.com")
    physical_assessment_repository.seed(_make_physical_assessment(client.id, uuid.uuid4()))
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        client_user_id, RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/physical-assessments/client/{client.id}")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["client_id"] == str(client.id)


def test_client_cannot_view_other_clients_physical_assessments():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    other_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    client_repository.seed(other_client, "other@example.com")
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        client_user_id, RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/physical-assessments/client/{other_client.id}")

    assert response.status_code == 403


def test_get_client_physical_assessments_returns_404_for_missing_client():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/physical-assessments/client/{uuid.uuid4()}")

    assert response.status_code == 404


# --- GET /api/v1/physical-assessments/client/{id}/latest ------------------------------


def test_latest_endpoint_computes_change_from_previous():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    now = datetime.now(timezone.utc)
    physical_assessment_repository.seed(
        _make_physical_assessment(
            client.id, trainer.id, weight_kg=82, waist_cm=94, recorded_at=now - timedelta(days=14)
        )
    )
    physical_assessment_repository.seed(
        _make_physical_assessment(client.id, trainer.id, weight_kg=80, waist_cm=92, recorded_at=now)
    )
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/physical-assessments/client/{client.id}/latest")

    assert response.status_code == 200
    body = response.json()
    assert body["weight_kg"] == 80
    assert body["previous_weight_kg"] == 82
    assert body["weight_change"] == -2
    assert body["waist_cm"] == 92
    assert body["previous_waist_cm"] == 94
    assert body["waist_change"] == -2


def test_latest_endpoint_returns_null_change_without_previous():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    physical_assessment_repository.seed(_make_physical_assessment(client.id, trainer.id, weight_kg=80))
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/physical-assessments/client/{client.id}/latest")

    assert response.status_code == 200
    body = response.json()
    assert body["weight_kg"] == 80
    assert body["previous_weight_kg"] is None
    assert body["weight_change"] is None


def test_latest_endpoint_returns_404_without_any_physical_assessments():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    client, *_ = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/physical-assessments/client/{client.id}/latest")

    assert response.status_code == 404


# --- GET /api/v1/physical-assessments/{id} --------------------------------------------


def test_get_physical_assessment_by_id_succeeds_for_super_admin():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    physical_assessment = _make_physical_assessment(uuid.uuid4(), uuid.uuid4())
    physical_assessment_repository.seed(physical_assessment)
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/physical-assessments/{physical_assessment.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(physical_assessment.id)


def test_get_physical_assessment_by_id_returns_404_for_missing_physical_assessment():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/physical-assessments/{uuid.uuid4()}")

    assert response.status_code == 404


# --- GET /api/v1/physical-assessments (paginated list) --------------------------------


def test_list_physical_assessments_succeeds_for_super_admin():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    for _ in range(3):
        physical_assessment_repository.seed(_make_physical_assessment(uuid.uuid4(), uuid.uuid4()))
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/physical-assessments?page=1&page_size=2")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2


# --- PATCH /api/v1/physical-assessments/{id} -------------------------------------------


def test_update_physical_assessment_succeeds_within_edit_window():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    physical_assessment = _make_physical_assessment(client.id, trainer.id, weight_kg=80)
    physical_assessment_repository.seed(physical_assessment)
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.patch(
        f"/api/v1/physical-assessments/{physical_assessment.id}", json={"weight_kg": 78}
    )

    assert response.status_code == 200
    assert response.json()["weight_kg"] == 78


def test_update_physical_assessment_rejects_after_edit_window_expired():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    setting_repository.seed(
        ApplicationSetting(
            id=uuid.uuid4(),
            key="physical_assessment_edit_window_days",
            value="1",
            description="Edit window",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    physical_assessment = _make_physical_assessment(
        client.id, trainer.id, weight_kg=80,
        recorded_at=datetime.now(timezone.utc) - timedelta(days=5),
    )
    physical_assessment_repository.seed(physical_assessment)
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.patch(
        f"/api/v1/physical-assessments/{physical_assessment.id}", json={"weight_kg": 78}
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "This physical assessment can no longer be modified. The configured edit window "
            "has expired."
        )
    }


def test_update_physical_assessment_rejects_client_role():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    client, trainer, _ = _setup_assigned_pair(client_repository, assignment_repository)
    physical_assessment = _make_physical_assessment(client.id, trainer.id, weight_kg=80)
    physical_assessment_repository.seed(physical_assessment)
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        uuid.uuid4(), RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.patch(
        f"/api/v1/physical-assessments/{physical_assessment.id}", json={"weight_kg": 78}
    )

    assert response.status_code == 403


def test_update_physical_assessment_returns_404_for_missing_physical_assessment():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        uuid.uuid4(), RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.patch(
        f"/api/v1/physical-assessments/{uuid.uuid4()}", json={"weight_kg": 78}
    )

    assert response.status_code == 404


# --- GET /api/v1/physical-assessments/pending -------------------------------------------


def test_pending_physical_assessments_allowed_for_trainer():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    client, trainer, trainer_user_id = _setup_assigned_pair(
        client_repository, assignment_repository
    )
    physical_assessment_repository.seed_latest_row(
        LatestPhysicalAssessmentRow(
            client_id=client.id,
            client_name=f"{client.first_name} {client.last_name}",
            recorded_at=datetime.now(timezone.utc) - timedelta(days=20),
        )
    )
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        trainer_user_id, RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/physical-assessments/pending")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["client_id"] == str(client.id)
    assert body[0]["days_overdue"] == 6


def test_pending_physical_assessments_returns_empty_list_when_none_pending():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    _, _, trainer_user_id = _setup_assigned_pair(client_repository, assignment_repository)
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        trainer_user_id, RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/physical-assessments/pending")

    assert response.status_code == 200
    assert response.json() == []


def test_pending_physical_assessments_rejects_client_role():
    physical_assessment_repository, client_repository, assignment_repository, setting_repository = (
        _make_repos()
    )
    _override_dependencies(
        physical_assessment_repository, client_repository, assignment_repository, setting_repository,
        uuid.uuid4(), RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/physical-assessments/pending")

    assert response.status_code == 403


# --- Existing functionality remains unaffected --------------------------------


def test_existing_sessions_endpoint_unaffected_by_physical_assessments_module():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/sessions")

    # Unauthenticated request still behaves exactly as before (401), proving
    # the sessions router/module was not disturbed by adding physical_assessments.
    assert response.status_code == 401


def test_health_endpoint_unaffected():
    test_client = TestClient(app)

    response = test_client.get("/health")

    assert response.status_code == 200
