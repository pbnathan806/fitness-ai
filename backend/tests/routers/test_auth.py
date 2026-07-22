import uuid

from fastapi.testclient import TestClient

from core.deps import CurrentUser, get_current_user
from core.security import create_access_token, hash_password
from main import app
from models.user import User
from routers.auth import get_role_repository, get_user_repository
from tests.services.test_auth_service import FakeRoleRepository, FakeUserRepository


def _override_dependencies(user: User | None, roles: list[str]) -> None:
    app.dependency_overrides[get_user_repository] = lambda: FakeUserRepository(user)
    app.dependency_overrides[get_role_repository] = lambda: FakeRoleRepository(roles)


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_login_endpoint_returns_token_and_roles_for_valid_credentials():
    user = User(
        id=uuid.uuid4(),
        email="trainer@example.com",
        password_hash=hash_password("Str0ngPassword!"),
    )
    _override_dependencies(user, ["TRAINER"])
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "trainer@example.com", "password": "Str0ngPassword!"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["roles"] == ["TRAINER"]
    assert body["user_id"] == str(user.id)
    assert body["access_token"]


def test_login_endpoint_rejects_invalid_credentials():
    user = User(
        id=uuid.uuid4(),
        email="trainer@example.com",
        password_hash=hash_password("Str0ngPassword!"),
    )
    _override_dependencies(user, ["TRAINER"])
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "trainer@example.com", "password": "WrongPassword!"},
    )

    assert response.status_code == 401


def test_login_endpoint_rejects_malformed_email():
    _override_dependencies(None, [])
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "not-an-email", "password": "Str0ngPassword!"},
    )

    assert response.status_code == 422


def test_get_roles_endpoint_returns_assigned_roles_and_active_role():
    user_id = uuid.uuid4()
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=user_id, active_role="TRAINER"
    )
    app.dependency_overrides[get_user_repository] = lambda: FakeUserRepository(None)
    app.dependency_overrides[get_role_repository] = lambda: FakeRoleRepository(
        ["SUPER_ADMIN", "TRAINER"]
    )
    client = TestClient(app)

    response = client.get(
        "/api/v1/auth/roles", headers={"Authorization": "Bearer irrelevant"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["roles"] == ["SUPER_ADMIN", "TRAINER"]
    assert body["active_role"] == "TRAINER"


def test_get_roles_endpoint_requires_authentication():
    client = TestClient(app)

    response = client.get("/api/v1/auth/roles")

    assert response.status_code == 401


def test_get_roles_endpoint_rejects_invalid_token():
    client = TestClient(app)

    response = client.get(
        "/api/v1/auth/roles", headers={"Authorization": "Bearer not-a-valid-token"}
    )

    assert response.status_code == 401


def test_switch_role_endpoint_succeeds_for_assigned_role():
    user_id = uuid.uuid4()
    token = create_access_token(subject=str(user_id))
    app.dependency_overrides[get_user_repository] = lambda: FakeUserRepository(None)
    app.dependency_overrides[get_role_repository] = lambda: FakeRoleRepository(
        ["SUPER_ADMIN", "TRAINER"]
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/switch-role",
        json={"role": "TRAINER"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["active_role"] == "TRAINER"
    assert body["roles"] == ["SUPER_ADMIN", "TRAINER"]
    assert body["access_token"]


def test_switch_role_endpoint_rejects_unassigned_role():
    user_id = uuid.uuid4()
    token = create_access_token(subject=str(user_id))
    app.dependency_overrides[get_user_repository] = lambda: FakeUserRepository(None)
    app.dependency_overrides[get_role_repository] = lambda: FakeRoleRepository(
        ["TRAINER"]
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/switch-role",
        json={"role": "SUPER_ADMIN"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_switch_role_endpoint_requires_authentication():
    app.dependency_overrides[get_role_repository] = lambda: FakeRoleRepository(
        ["TRAINER"]
    )
    client = TestClient(app)

    response = client.post("/api/v1/auth/switch-role", json={"role": "TRAINER"})

    assert response.status_code == 401
