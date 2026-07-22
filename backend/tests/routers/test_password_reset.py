import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from core.security import hash_password, verify_password
from main import app
from models.user import User
from routers.auth import (
    get_password_reset_notifier,
    get_password_reset_token_repository,
    get_user_repository,
)
from tests.services.test_password_reset_service import (
    FakePasswordResetNotifier,
    FakePasswordResetTokenRepository,
    FakeUserRepository,
)


def _override_dependencies(
    user: User | None,
    user_repository: FakeUserRepository,
    token_repository: FakePasswordResetTokenRepository,
    notifier: FakePasswordResetNotifier,
) -> None:
    app.dependency_overrides[get_user_repository] = lambda: user_repository
    app.dependency_overrides[get_password_reset_token_repository] = lambda: token_repository
    app.dependency_overrides[get_password_reset_notifier] = lambda: notifier


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_forgot_password_returns_generic_message_for_known_email():
    user = User(
        id=uuid.uuid4(),
        email="trainer@example.com",
        password_hash=hash_password("Str0ngPassword!"),
    )
    notifier = FakePasswordResetNotifier()
    _override_dependencies(
        user, FakeUserRepository(user), FakePasswordResetTokenRepository(), notifier
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/forgot-password", json={"email": "trainer@example.com"}
    )

    assert response.status_code == 200
    assert len(notifier.sent) == 1


def test_forgot_password_returns_generic_message_for_unknown_email():
    notifier = FakePasswordResetNotifier()
    _override_dependencies(
        None, FakeUserRepository(None), FakePasswordResetTokenRepository(), notifier
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/forgot-password", json={"email": "missing@example.com"}
    )

    assert response.status_code == 200
    assert notifier.sent == []


def test_forgot_password_rejects_malformed_email():
    _override_dependencies(
        None, FakeUserRepository(None), FakePasswordResetTokenRepository(), FakePasswordResetNotifier()
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/forgot-password", json={"email": "not-an-email"}
    )

    assert response.status_code == 422


def test_reset_password_succeeds_with_valid_token():
    user = User(
        id=uuid.uuid4(),
        email="trainer@example.com",
        password_hash=hash_password("Str0ngPassword!"),
    )
    user_repository = FakeUserRepository(user)
    token_repository = FakePasswordResetTokenRepository()
    notifier = FakePasswordResetNotifier()
    _override_dependencies(user, user_repository, token_repository, notifier)
    client = TestClient(app)

    client.post("/api/v1/auth/forgot-password", json={"email": "trainer@example.com"})
    _, raw_token = notifier.sent[0]

    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewStr0ngPassword!"},
    )

    assert response.status_code == 200
    assert verify_password("NewStr0ngPassword!", user.password_hash)


def test_reset_password_rejects_invalid_token():
    _override_dependencies(
        None, FakeUserRepository(None), FakePasswordResetTokenRepository(), FakePasswordResetNotifier()
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "not-a-real-token", "new_password": "NewStr0ngPassword!"},
    )

    assert response.status_code == 400


def test_reset_password_rejects_expired_token():
    user = User(
        id=uuid.uuid4(),
        email="trainer@example.com",
        password_hash=hash_password("Str0ngPassword!"),
    )
    user_repository = FakeUserRepository(user)
    token_repository = FakePasswordResetTokenRepository()
    notifier = FakePasswordResetNotifier()
    _override_dependencies(user, user_repository, token_repository, notifier)
    client = TestClient(app)

    client.post("/api/v1/auth/forgot-password", json={"email": "trainer@example.com"})
    _, raw_token = notifier.sent[0]
    for token in token_repository._tokens.values():
        token.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewStr0ngPassword!"},
    )

    assert response.status_code == 400


def test_reset_password_rejects_short_new_password():
    _override_dependencies(
        None, FakeUserRepository(None), FakePasswordResetTokenRepository(), FakePasswordResetNotifier()
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "some-token", "new_password": "short"},
    )

    assert response.status_code == 422
