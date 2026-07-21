import uuid

from fastapi.testclient import TestClient

from core.security import hash_password
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
