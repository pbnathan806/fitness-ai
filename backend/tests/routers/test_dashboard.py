import uuid

from fastapi.testclient import TestClient

from core.constants import RoleName
from core.deps import CurrentUser, get_current_user
from main import app
from routers.dashboard import (
    get_application_setting_repository,
    get_assignment_repository,
    get_check_in_repository,
    get_client_repository,
    get_dashboard_repository,
    get_measurement_repository,
    get_session_repository,
    get_subscription_repository,
)
from tests.services.test_application_setting_service import (
    FakeApplicationSettingRepository,
    _make_setting,
)
from tests.services.test_assignment_service import FakeAssignmentRepository
from tests.services.test_check_in_service import FakeCheckInRepository
from tests.services.test_client_service import FakeClientRepository
from tests.services.test_dashboard_service import FakeDashboardRepository, _build_shared_fixture
from tests.services.test_measurement_service import FakeMeasurementRepository
from tests.services.test_session_service import FakeSessionRepository
from tests.services.test_subscription_service import FakeSubscriptionRepository


def _override_dependencies(
    user_id: uuid.UUID,
    active_role: str | None,
    *,
    dashboard_repository=None,
    client_repository=None,
    assignment_repository=None,
    session_repository=None,
    check_in_repository=None,
    measurement_repository=None,
    subscription_repository=None,
    application_setting_repository=None,
) -> None:
    app.dependency_overrides[get_dashboard_repository] = lambda: (
        dashboard_repository or FakeDashboardRepository()
    )
    app.dependency_overrides[get_client_repository] = lambda: (
        client_repository or FakeClientRepository()
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
    app.dependency_overrides[get_measurement_repository] = lambda: (
        measurement_repository or FakeMeasurementRepository()
    )
    app.dependency_overrides[get_subscription_repository] = lambda: (
        subscription_repository or FakeSubscriptionRepository()
    )
    app.dependency_overrides[get_application_setting_repository] = lambda: (
        application_setting_repository or FakeApplicationSettingRepository()
    )
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=user_id, active_role=active_role
    )


def _seeded_application_setting_repository() -> FakeApplicationSettingRepository:
    repository = FakeApplicationSettingRepository()
    repository.seed(_make_setting(key="measurement_overdue_days", value="14"))
    repository.seed(_make_setting(key="subscription_expired_days", value="30"))
    return repository


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_trainer_dashboard_requires_authentication():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/dashboard/trainer")

    assert response.status_code == 401


def test_trainer_dashboard_rejects_non_trainer():
    _override_dependencies(uuid.uuid4(), RoleName.CLIENT)
    test_client = TestClient(app)

    response = test_client.get("/api/v1/dashboard/trainer")

    assert response.status_code == 403


def test_trainer_dashboard_returns_404_without_trainer_profile():
    _override_dependencies(uuid.uuid4(), RoleName.TRAINER)
    test_client = TestClient(app)

    response = test_client.get("/api/v1/dashboard/trainer")

    assert response.status_code == 404


def test_trainer_dashboard_succeeds_for_trainer():
    fixture = _build_shared_fixture()
    _override_dependencies(
        fixture["trainer_user_id"],
        RoleName.TRAINER,
        dashboard_repository=fixture["dashboard_repository"],
        client_repository=fixture["client_repository"],
        assignment_repository=fixture["assignment_repository"],
        session_repository=fixture["session_repository"],
        check_in_repository=fixture["check_in_repository"],
        measurement_repository=fixture["measurement_repository"],
        subscription_repository=fixture["subscription_repository"],
        application_setting_repository=_seeded_application_setting_repository(),
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/dashboard/trainer")

    assert response.status_code == 200
    body = response.json()
    assert body["assigned_clients"] == 2
    assert body["active_clients"] == 1
    assert body["pending_measurements"] == 1


def test_super_admin_dashboard_requires_authentication():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/dashboard/super-admin")

    assert response.status_code == 401


def test_super_admin_dashboard_rejects_non_super_admin():
    _override_dependencies(uuid.uuid4(), RoleName.TRAINER)
    test_client = TestClient(app)

    response = test_client.get("/api/v1/dashboard/super-admin")

    assert response.status_code == 403


def test_super_admin_dashboard_succeeds_for_super_admin():
    fixture = _build_shared_fixture()
    _override_dependencies(
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
        dashboard_repository=fixture["dashboard_repository"],
        client_repository=fixture["client_repository"],
        assignment_repository=fixture["assignment_repository"],
        session_repository=fixture["session_repository"],
        check_in_repository=fixture["check_in_repository"],
        measurement_repository=fixture["measurement_repository"],
        subscription_repository=fixture["subscription_repository"],
        application_setting_repository=_seeded_application_setting_repository(),
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/dashboard/super-admin")

    assert response.status_code == 200
    body = response.json()
    assert body["total_clients"] == 2
    assert body["active_clients"] == 1
    assert body["expired_clients"] == 1
    assert body["total_trainers"] == 1


def test_client_dashboard_requires_authentication():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/dashboard/client")

    assert response.status_code == 401


def test_client_dashboard_rejects_non_client():
    _override_dependencies(uuid.uuid4(), RoleName.TRAINER)
    test_client = TestClient(app)

    response = test_client.get("/api/v1/dashboard/client")

    assert response.status_code == 403


def test_client_dashboard_returns_404_without_client_profile():
    _override_dependencies(uuid.uuid4(), RoleName.CLIENT)
    test_client = TestClient(app)

    response = test_client.get("/api/v1/dashboard/client")

    assert response.status_code == 404


def test_client_dashboard_succeeds_for_client():
    from tests.services.test_dashboard_service import _build_client_fixture

    fixture = _build_client_fixture(sessions_per_week=3)
    _override_dependencies(
        fixture["user_id"],
        RoleName.CLIENT,
        client_repository=fixture["client_repository"],
        session_repository=fixture["session_repository"],
        check_in_repository=fixture["check_in_repository"],
        subscription_repository=fixture["subscription_repository"],
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/dashboard/client")

    assert response.status_code == 200
    body = response.json()
    assert body["target_check_ins"] == 3
    assert body["check_ins_this_week"] == 0
    assert body["check_in_adherence_percentage"] == 0
