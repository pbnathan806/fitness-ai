import uuid

from fastapi.testclient import TestClient

from core.constants import RoleName
from core.deps import CurrentUser, get_current_user
from main import app
from routers.application_settings import get_application_setting_repository
from tests.services.test_application_setting_service import (
    FakeApplicationSettingRepository,
    _make_setting,
)


def _override_dependencies(
    repository: FakeApplicationSettingRepository, user_id: uuid.UUID, active_role: str | None
) -> None:
    app.dependency_overrides[get_application_setting_repository] = lambda: repository
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=user_id, active_role=active_role
    )


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_list_settings_succeeds_for_super_admin():
    repository = FakeApplicationSettingRepository()
    repository.seed(_make_setting(key="measurement_overdue_days", value="14"))
    repository.seed(_make_setting(key="subscription_expired_days", value="30"))
    _override_dependencies(repository, uuid.uuid4(), RoleName.SUPER_ADMIN)
    test_client = TestClient(app)

    response = test_client.get("/api/v1/application-settings")

    assert response.status_code == 200
    assert {item["key"] for item in response.json()} == {
        "measurement_overdue_days",
        "subscription_expired_days",
    }


def test_list_settings_rejects_trainer_role():
    repository = FakeApplicationSettingRepository()
    _override_dependencies(repository, uuid.uuid4(), RoleName.TRAINER)
    test_client = TestClient(app)

    response = test_client.get("/api/v1/application-settings")

    assert response.status_code == 403


def test_list_settings_rejects_client_role():
    repository = FakeApplicationSettingRepository()
    _override_dependencies(repository, uuid.uuid4(), RoleName.CLIENT)
    test_client = TestClient(app)

    response = test_client.get("/api/v1/application-settings")

    assert response.status_code == 403


def test_list_settings_requires_authentication():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/application-settings")

    assert response.status_code == 401


def test_get_setting_succeeds_for_super_admin():
    repository = FakeApplicationSettingRepository()
    setting = _make_setting(key="measurement_overdue_days", value="14")
    repository.seed(setting)
    _override_dependencies(repository, uuid.uuid4(), RoleName.SUPER_ADMIN)
    test_client = TestClient(app)

    response = test_client.get("/api/v1/application-settings/measurement_overdue_days")

    assert response.status_code == 200
    assert response.json()["value"] == "14"


def test_get_setting_rejects_trainer_role():
    repository = FakeApplicationSettingRepository()
    repository.seed(_make_setting(key="measurement_overdue_days", value="14"))
    _override_dependencies(repository, uuid.uuid4(), RoleName.TRAINER)
    test_client = TestClient(app)

    response = test_client.get("/api/v1/application-settings/measurement_overdue_days")

    assert response.status_code == 403


def test_get_setting_returns_404_for_missing_key():
    repository = FakeApplicationSettingRepository()
    _override_dependencies(repository, uuid.uuid4(), RoleName.SUPER_ADMIN)
    test_client = TestClient(app)

    response = test_client.get("/api/v1/application-settings/does_not_exist")

    assert response.status_code == 404


def test_update_setting_succeeds_for_super_admin():
    repository = FakeApplicationSettingRepository()
    repository.seed(_make_setting(key="measurement_overdue_days", value="14"))
    _override_dependencies(repository, uuid.uuid4(), RoleName.SUPER_ADMIN)
    test_client = TestClient(app)

    response = test_client.patch(
        "/api/v1/application-settings/measurement_overdue_days", json={"value": "21"}
    )

    assert response.status_code == 200
    assert response.json()["value"] == "21"


def test_update_setting_rejects_trainer_role():
    repository = FakeApplicationSettingRepository()
    repository.seed(_make_setting(key="measurement_overdue_days", value="14"))
    _override_dependencies(repository, uuid.uuid4(), RoleName.TRAINER)
    test_client = TestClient(app)

    response = test_client.patch(
        "/api/v1/application-settings/measurement_overdue_days", json={"value": "21"}
    )

    assert response.status_code == 403


def test_update_setting_rejects_client_role():
    repository = FakeApplicationSettingRepository()
    repository.seed(_make_setting(key="measurement_overdue_days", value="14"))
    _override_dependencies(repository, uuid.uuid4(), RoleName.CLIENT)
    test_client = TestClient(app)

    response = test_client.patch(
        "/api/v1/application-settings/measurement_overdue_days", json={"value": "21"}
    )

    assert response.status_code == 403


def test_update_setting_requires_authentication():
    test_client = TestClient(app)

    response = test_client.patch(
        "/api/v1/application-settings/measurement_overdue_days", json={"value": "21"}
    )

    assert response.status_code == 401


def test_update_setting_returns_404_for_missing_key():
    repository = FakeApplicationSettingRepository()
    _override_dependencies(repository, uuid.uuid4(), RoleName.SUPER_ADMIN)
    test_client = TestClient(app)

    response = test_client.patch(
        "/api/v1/application-settings/does_not_exist", json={"value": "21"}
    )

    assert response.status_code == 404


def test_update_setting_rejects_empty_value():
    repository = FakeApplicationSettingRepository()
    repository.seed(_make_setting(key="measurement_overdue_days", value="14"))
    _override_dependencies(repository, uuid.uuid4(), RoleName.SUPER_ADMIN)
    test_client = TestClient(app)

    response = test_client.patch(
        "/api/v1/application-settings/measurement_overdue_days", json={"value": ""}
    )

    assert response.status_code == 422
