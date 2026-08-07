import asyncio
import uuid
from datetime import datetime, time, timezone

from fastapi.testclient import TestClient

from core.constants import RoleName
from core.deps import CurrentUser, get_current_user
from main import app
from models.trainer_availability import TrainerAvailability
from routers.trainers import (
    get_application_setting_service,
    get_assignment_repository,
    get_check_in_repository,
    get_dashboard_repository,
    get_physical_assessment_repository,
    get_role_repository,
    get_session_repository,
    get_trainer_availability_repository,
    get_trainer_repository,
    get_user_repository,
)
from services.application_setting_service import ApplicationSettingService
from tests.services.test_application_setting_service import (
    FakeApplicationSettingRepository,
    _make_setting,
)
from tests.services.test_assignment_service import FakeAssignmentRepository, _make_trainer
from tests.services.test_check_in_service import FakeCheckInRepository
from tests.services.test_client_service import FakeUserRepository
from tests.services.test_dashboard_service import FakeDashboardRepository
from tests.services.test_physical_assessment_service import FakePhysicalAssessmentRepository
from tests.services.test_session_service import FakeSessionRepository
from tests.services.test_trainer_service import (
    FakeRoleRepository,
    FakeTrainerAvailabilityRepository,
    FakeTrainerRepository,
)


def _make_seeded_trainer(user_id: uuid.UUID, **overrides):
    """`_make_trainer` doesn't default created_at/updated_at (it's only ever used via
    a repository's create(), which sets them); router responses require real
    datetimes, so seed with them explicitly here.
    """
    now = datetime.now(timezone.utc)
    overrides.setdefault("created_at", now)
    overrides.setdefault("updated_at", now)
    return _make_trainer(user_id=user_id, **overrides)


def _application_setting_service() -> ApplicationSettingService:
    repository = FakeApplicationSettingRepository()
    repository.seed(_make_setting(key="physical_assessment_overdue_days", value="14"))
    return ApplicationSettingService(repository)


def _override_dependencies(
    *,
    trainer_repository=None,
    user_repository=None,
    role_repository=None,
    assignment_repository=None,
    session_repository=None,
    check_in_repository=None,
    physical_assessment_repository=None,
    trainer_availability_repository=None,
    dashboard_repository=None,
    application_setting_service=None,
    user_id: uuid.UUID,
    active_role: str | None,
) -> None:
    app.dependency_overrides[get_trainer_repository] = lambda: (
        trainer_repository or FakeTrainerRepository()
    )
    app.dependency_overrides[get_user_repository] = lambda: (
        user_repository or FakeUserRepository()
    )
    app.dependency_overrides[get_role_repository] = lambda: (
        role_repository or FakeRoleRepository()
    )
    app.dependency_overrides[get_assignment_repository] = lambda: (
        assignment_repository or FakeAssignmentRepository()
    )
    app.dependency_overrides[get_session_repository] = lambda: (
        session_repository or FakeSessionRepository()
    )
    app.dependency_overrides[get_check_in_repository] = lambda: (
        check_in_repository or FakeCheckInRepository()
    )
    app.dependency_overrides[get_physical_assessment_repository] = lambda: (
        physical_assessment_repository or FakePhysicalAssessmentRepository()
    )
    app.dependency_overrides[get_trainer_availability_repository] = lambda: (
        trainer_availability_repository or FakeTrainerAvailabilityRepository()
    )
    app.dependency_overrides[get_dashboard_repository] = lambda: (
        dashboard_repository or FakeDashboardRepository()
    )
    app.dependency_overrides[get_application_setting_service] = lambda: (
        application_setting_service or _application_setting_service()
    )
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=user_id, active_role=active_role
    )


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_create_trainer_succeeds_for_super_admin():
    _override_dependencies(user_id=uuid.uuid4(), active_role=RoleName.SUPER_ADMIN)
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/trainers",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "trainer@example.com",
            "phone_number": "+15551234567",
            "timezone": "America/New_York",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert len(body["temporary_password"]) > 0


def test_create_trainer_rejects_trainer_and_client():
    for role in (RoleName.TRAINER, RoleName.CLIENT):
        _override_dependencies(user_id=uuid.uuid4(), active_role=role)
        test_client = TestClient(app)

        response = test_client.post(
            "/api/v1/trainers",
            json={
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "trainer@example.com",
                "timezone": "America/New_York",
            },
        )
        assert response.status_code == 403


def test_create_trainer_requires_authentication():
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/trainers",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "trainer@example.com",
            "timezone": "America/New_York",
        },
    )

    assert response.status_code == 401


def test_list_trainers_succeeds_for_super_admin_with_pagination():
    trainer_repository = FakeTrainerRepository()
    for name in ("Alice", "Bob", "Carol"):
        trainer_repository.seed(
            _make_seeded_trainer(user_id=uuid.uuid4(), first_name=name, last_name="Doe"),
            f"{name.lower()}@example.com",
        )
    _override_dependencies(
        trainer_repository=trainer_repository,
        user_id=uuid.uuid4(),
        active_role=RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/trainers", params={"page": 1, "page_size": 2})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["total_pages"] == 2


def test_list_trainers_rejects_trainer_and_client():
    for role in (RoleName.TRAINER, RoleName.CLIENT):
        _override_dependencies(user_id=uuid.uuid4(), active_role=role)
        test_client = TestClient(app)

        response = test_client.get("/api/v1/trainers")
        assert response.status_code == 403


def test_get_trainer_by_id_succeeds_for_super_admin():
    trainer_repository = FakeTrainerRepository()
    trainer = _make_seeded_trainer(user_id=uuid.uuid4(), first_name="Jane", last_name="Doe")
    trainer_repository.seed(trainer, "jane@example.com")
    _override_dependencies(
        trainer_repository=trainer_repository,
        user_id=uuid.uuid4(),
        active_role=RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/trainers/{trainer.id}")

    assert response.status_code == 200
    assert response.json()["email"] == "jane@example.com"


def test_get_trainer_by_id_rejects_other_trainer():
    trainer_repository = FakeTrainerRepository()
    trainer = _make_trainer(user_id=uuid.uuid4())
    trainer_repository.seed(trainer)
    _override_dependencies(
        trainer_repository=trainer_repository,
        user_id=uuid.uuid4(),
        active_role=RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/trainers/{trainer.id}")

    assert response.status_code == 403


def test_get_trainer_by_id_rejects_client():
    trainer_repository = FakeTrainerRepository()
    trainer = _make_trainer(user_id=uuid.uuid4())
    trainer_repository.seed(trainer)
    _override_dependencies(
        trainer_repository=trainer_repository,
        user_id=uuid.uuid4(),
        active_role=RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/trainers/{trainer.id}")

    assert response.status_code == 403


def test_get_trainer_by_id_returns_404_when_missing():
    _override_dependencies(user_id=uuid.uuid4(), active_role=RoleName.SUPER_ADMIN)
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/trainers/{uuid.uuid4()}")

    assert response.status_code == 404


def test_get_trainer_availability_succeeds_for_super_admin():
    trainer_repository = FakeTrainerRepository()
    trainer = _make_seeded_trainer(user_id=uuid.uuid4())
    trainer_repository.seed(trainer)
    trainer_availability_repository = FakeTrainerAvailabilityRepository()
    asyncio.run(
        trainer_availability_repository.create(
            TrainerAvailability(
                trainer_id=trainer.id,
                weekday=1,
                start_time=time(9, 0),
                end_time=time(10, 0),
                is_available=True,
            )
        )
    )
    _override_dependencies(
        trainer_repository=trainer_repository,
        trainer_availability_repository=trainer_availability_repository,
        user_id=uuid.uuid4(),
        active_role=RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/trainers/{trainer.id}/availability")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["weekday"] == 1


def test_get_trainer_availability_rejects_other_trainer():
    trainer_repository = FakeTrainerRepository()
    trainer = _make_trainer(user_id=uuid.uuid4())
    trainer_repository.seed(trainer)
    _override_dependencies(
        trainer_repository=trainer_repository,
        user_id=uuid.uuid4(),
        active_role=RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/trainers/{trainer.id}/availability")

    assert response.status_code == 403


def test_get_trainer_availability_rejects_client():
    trainer_repository = FakeTrainerRepository()
    trainer = _make_trainer(user_id=uuid.uuid4())
    trainer_repository.seed(trainer)
    _override_dependencies(
        trainer_repository=trainer_repository,
        user_id=uuid.uuid4(),
        active_role=RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/trainers/{trainer.id}/availability")

    assert response.status_code == 403


def test_get_trainer_availability_returns_404_when_missing():
    _override_dependencies(user_id=uuid.uuid4(), active_role=RoleName.SUPER_ADMIN)
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/trainers/{uuid.uuid4()}/availability")

    assert response.status_code == 404


def test_get_current_trainer_succeeds_for_trainer():
    trainer_repository = FakeTrainerRepository()
    trainer_user_id = uuid.uuid4()
    trainer = _make_seeded_trainer(user_id=trainer_user_id)
    trainer_repository.seed(trainer, "me@example.com")
    _override_dependencies(
        trainer_repository=trainer_repository,
        user_id=trainer_user_id,
        active_role=RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/trainers/me")

    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_get_current_trainer_rejects_super_admin_and_client():
    for role in (RoleName.SUPER_ADMIN, RoleName.CLIENT):
        _override_dependencies(user_id=uuid.uuid4(), active_role=role)
        test_client = TestClient(app)

        response = test_client.get("/api/v1/trainers/me")
        assert response.status_code == 403


def test_update_current_trainer_restricts_to_phone_and_timezone():
    trainer_repository = FakeTrainerRepository()
    trainer_user_id = uuid.uuid4()
    trainer = _make_seeded_trainer(user_id=trainer_user_id)
    trainer_repository.seed(trainer)
    _override_dependencies(
        trainer_repository=trainer_repository,
        user_id=trainer_user_id,
        active_role=RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.put(
        "/api/v1/trainers/me",
        json={"phone_number": "+15550001111", "timezone": "Asia/Kolkata"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["phone_number"] == "+15550001111"
    assert body["timezone"] == "Asia/Kolkata"


def test_update_trainer_status_succeeds_for_super_admin():
    trainer_repository = FakeTrainerRepository()
    role_repository = FakeRoleRepository()
    trainer_user_id = uuid.uuid4()
    trainer = _make_seeded_trainer(user_id=trainer_user_id, is_active=True)
    trainer_repository.seed(trainer)
    role_repository.seed_role_for_user(trainer_user_id, RoleName.TRAINER)
    _override_dependencies(
        trainer_repository=trainer_repository,
        role_repository=role_repository,
        user_id=uuid.uuid4(),
        active_role=RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.patch(
        f"/api/v1/trainers/{trainer.id}/status", json={"is_active": False}
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_update_trainer_status_rejects_non_super_admin():
    trainer_repository = FakeTrainerRepository()
    trainer = _make_trainer(user_id=uuid.uuid4())
    trainer_repository.seed(trainer)
    _override_dependencies(
        trainer_repository=trainer_repository,
        user_id=uuid.uuid4(),
        active_role=RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.patch(
        f"/api/v1/trainers/{trainer.id}/status", json={"is_active": False}
    )

    assert response.status_code == 403


def test_get_trainer_summary_returns_zero_metrics_for_new_trainer():
    trainer_repository = FakeTrainerRepository()
    trainer = _make_trainer(user_id=uuid.uuid4())
    trainer_repository.seed(trainer)
    _override_dependencies(
        trainer_repository=trainer_repository,
        user_id=uuid.uuid4(),
        active_role=RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/trainers/{trainer.id}/summary")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "assigned_clients": 0,
        "sessions_this_week": 0,
        "completed_sessions_this_month": 0,
        "pending_check_ins": 0,
        "pending_physical_assessments": 0,
    }


def test_get_trainer_performance_returns_zero_metrics_for_new_trainer():
    trainer_repository = FakeTrainerRepository()
    trainer = _make_trainer(user_id=uuid.uuid4())
    trainer_repository.seed(trainer)
    _override_dependencies(
        trainer_repository=trainer_repository,
        user_id=uuid.uuid4(),
        active_role=RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/trainers/{trainer.id}/performance")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "assigned_clients": 0,
        "completed_sessions": 0,
        "completion_rate": 0,
        "average_check_in_rate": 0,
    }


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------


def test_availability_crud_flow_for_trainer():
    trainer_repository = FakeTrainerRepository()
    trainer_user_id = uuid.uuid4()
    trainer_repository.seed(_make_trainer(user_id=trainer_user_id))
    availability_repository = FakeTrainerAvailabilityRepository()
    _override_dependencies(
        trainer_repository=trainer_repository,
        trainer_availability_repository=availability_repository,
        user_id=trainer_user_id,
        active_role=RoleName.TRAINER,
    )
    test_client = TestClient(app)

    create_response = test_client.post(
        "/api/v1/trainers/me/availability",
        json={
            "weekday": 0,
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "is_available": True,
        },
    )
    assert create_response.status_code == 201
    availability_id = create_response.json()["id"]

    list_response = test_client.get("/api/v1/trainers/me/availability")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = test_client.put(
        f"/api/v1/trainers/me/availability/{availability_id}",
        json={
            "weekday": 1,
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "is_available": False,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["weekday"] == 1

    delete_response = test_client.delete(
        f"/api/v1/trainers/me/availability/{availability_id}"
    )
    assert delete_response.status_code == 204

    list_after_delete = test_client.get("/api/v1/trainers/me/availability")
    assert list_after_delete.json() == []


def test_create_availability_rejects_overlap():
    trainer_repository = FakeTrainerRepository()
    trainer_user_id = uuid.uuid4()
    trainer_repository.seed(_make_trainer(user_id=trainer_user_id))
    availability_repository = FakeTrainerAvailabilityRepository()
    _override_dependencies(
        trainer_repository=trainer_repository,
        trainer_availability_repository=availability_repository,
        user_id=trainer_user_id,
        active_role=RoleName.TRAINER,
    )
    test_client = TestClient(app)

    test_client.post(
        "/api/v1/trainers/me/availability",
        json={
            "weekday": 0,
            "start_time": "09:00:00",
            "end_time": "11:00:00",
            "is_available": True,
        },
    )

    response = test_client.post(
        "/api/v1/trainers/me/availability",
        json={
            "weekday": 0,
            "start_time": "10:00:00",
            "end_time": "12:00:00",
            "is_available": True,
        },
    )

    assert response.status_code == 409


def test_create_availability_rejects_invalid_time_range():
    trainer_repository = FakeTrainerRepository()
    trainer_user_id = uuid.uuid4()
    trainer_repository.seed(_make_trainer(user_id=trainer_user_id))
    _override_dependencies(
        trainer_repository=trainer_repository,
        user_id=trainer_user_id,
        active_role=RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/trainers/me/availability",
        json={
            "weekday": 0,
            "start_time": "11:00:00",
            "end_time": "09:00:00",
            "is_available": True,
        },
    )

    assert response.status_code == 422


def test_availability_rejects_non_trainer():
    for role in (RoleName.SUPER_ADMIN, RoleName.CLIENT):
        _override_dependencies(user_id=uuid.uuid4(), active_role=role)
        test_client = TestClient(app)

        response = test_client.get("/api/v1/trainers/me/availability")
        assert response.status_code == 403
