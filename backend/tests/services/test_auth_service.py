import asyncio
import uuid
from datetime import datetime, timezone

import pytest

from core.security import hash_password, verify_password
from models.user import User
from repositories.role_repository import RoleRepository
from repositories.user_repository import UserRepository
from services.auth_service import (
    AuthService,
    IncorrectPasswordError,
    InvalidCredentialsError,
    RoleNotAssignedError,
    UserNotFoundError,
)


class FakeUserRepository(UserRepository):
    def __init__(self, user: User | None) -> None:
        self._user = user
        self.last_login_calls: list[tuple[uuid.UUID, datetime]] = []
        self.password_hash_calls: list[tuple[uuid.UUID, str]] = []

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        if self._user is not None and self._user.id == user_id:
            return self._user
        return None

    async def get_by_email(self, email: str) -> User | None:
        if self._user is not None and self._user.email == email:
            return self._user
        return None

    async def update_last_login(self, user_id: uuid.UUID, login_time: datetime) -> None:
        self.last_login_calls.append((user_id, login_time))

    async def update_password_hash(self, user_id: uuid.UUID, password_hash: str) -> None:
        self.password_hash_calls.append((user_id, password_hash))
        if self._user is not None and self._user.id == user_id:
            self._user.password_hash = password_hash

    async def create(self, email: str, password_hash: str) -> User:
        raise NotImplementedError


class FakeRoleRepository(RoleRepository):
    def __init__(self, roles: list[str]) -> None:
        self._roles = roles

    async def get_role_names_for_user(self, user_id: uuid.UUID) -> list[str]:
        return self._roles

    async def get_by_name(self, name: str) -> None:
        raise NotImplementedError

    async def assign_role_to_user(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        raise NotImplementedError


def _make_user(email: str, password: str) -> User:
    return User(id=uuid.uuid4(), email=email, password_hash=hash_password(password))


def test_login_succeeds_with_valid_credentials():
    user = _make_user("trainer@example.com", "Str0ngPassword!")
    user_repository = FakeUserRepository(user)
    role_repository = FakeRoleRepository(["TRAINER"])
    service = AuthService(user_repository, role_repository)

    session = asyncio.run(service.login("trainer@example.com", "Str0ngPassword!"))

    assert session.user_id == user.id
    assert session.roles == ["TRAINER"]
    assert session.token_type == "bearer"
    assert session.access_token


def test_login_updates_last_login_at_on_success():
    user = _make_user("trainer@example.com", "Str0ngPassword!")
    user_repository = FakeUserRepository(user)
    role_repository = FakeRoleRepository(["TRAINER"])
    service = AuthService(user_repository, role_repository)

    before = datetime.now(timezone.utc)
    asyncio.run(service.login("trainer@example.com", "Str0ngPassword!"))

    assert len(user_repository.last_login_calls) == 1
    called_user_id, called_login_time = user_repository.last_login_calls[0]
    assert called_user_id == user.id
    assert called_login_time >= before
    assert called_login_time.tzinfo is not None


def test_login_raises_for_unknown_email():
    user_repository = FakeUserRepository(None)
    role_repository = FakeRoleRepository([])
    service = AuthService(user_repository, role_repository)

    with pytest.raises(InvalidCredentialsError):
        asyncio.run(service.login("missing@example.com", "Str0ngPassword!"))


def test_login_raises_for_wrong_password():
    user = _make_user("trainer@example.com", "Str0ngPassword!")
    user_repository = FakeUserRepository(user)
    role_repository = FakeRoleRepository(["TRAINER"])
    service = AuthService(user_repository, role_repository)

    with pytest.raises(InvalidCredentialsError):
        asyncio.run(service.login("trainer@example.com", "WrongPassword!"))


def test_login_does_not_update_last_login_on_failure():
    user = _make_user("trainer@example.com", "Str0ngPassword!")
    user_repository = FakeUserRepository(user)
    role_repository = FakeRoleRepository(["TRAINER"])
    service = AuthService(user_repository, role_repository)

    with pytest.raises(InvalidCredentialsError):
        asyncio.run(service.login("trainer@example.com", "WrongPassword!"))

    assert user_repository.last_login_calls == []


def test_login_returns_multiple_assigned_roles():
    user = _make_user("admin@example.com", "Str0ngPassword!")
    user_repository = FakeUserRepository(user)
    role_repository = FakeRoleRepository(["SUPER_ADMIN", "TRAINER"])
    service = AuthService(user_repository, role_repository)

    session = asyncio.run(service.login("admin@example.com", "Str0ngPassword!"))

    assert session.roles == ["SUPER_ADMIN", "TRAINER"]


def test_list_assigned_roles_returns_roles_for_user():
    user = _make_user("admin@example.com", "Str0ngPassword!")
    user_repository = FakeUserRepository(user)
    role_repository = FakeRoleRepository(["SUPER_ADMIN", "TRAINER"])
    service = AuthService(user_repository, role_repository)

    roles = asyncio.run(service.list_assigned_roles(user.id))

    assert roles == ["SUPER_ADMIN", "TRAINER"]


def test_switch_role_succeeds_for_assigned_role():
    user = _make_user("admin@example.com", "Str0ngPassword!")
    user_repository = FakeUserRepository(user)
    role_repository = FakeRoleRepository(["SUPER_ADMIN", "TRAINER"])
    service = AuthService(user_repository, role_repository)

    selection = asyncio.run(service.switch_role(user.id, "TRAINER"))

    assert selection.active_role == "TRAINER"
    assert selection.roles == ["SUPER_ADMIN", "TRAINER"]
    assert selection.token_type == "bearer"
    assert selection.access_token


def test_switch_role_rejects_unassigned_role():
    user = _make_user("trainer@example.com", "Str0ngPassword!")
    user_repository = FakeUserRepository(user)
    role_repository = FakeRoleRepository(["TRAINER"])
    service = AuthService(user_repository, role_repository)

    with pytest.raises(RoleNotAssignedError):
        asyncio.run(service.switch_role(user.id, "SUPER_ADMIN"))


def test_change_password_succeeds_with_correct_current_password():
    user = _make_user("trainer@example.com", "Str0ngPassword!")
    user_repository = FakeUserRepository(user)
    role_repository = FakeRoleRepository(["TRAINER"])
    service = AuthService(user_repository, role_repository)

    asyncio.run(service.change_password(user.id, "Str0ngPassword!", "NewStr0ngPassword!"))

    assert len(user_repository.password_hash_calls) == 1
    assert verify_password("NewStr0ngPassword!", user.password_hash)


def test_change_password_rejects_incorrect_current_password():
    user = _make_user("trainer@example.com", "Str0ngPassword!")
    user_repository = FakeUserRepository(user)
    role_repository = FakeRoleRepository(["TRAINER"])
    service = AuthService(user_repository, role_repository)

    with pytest.raises(IncorrectPasswordError):
        asyncio.run(service.change_password(user.id, "WrongPassword!", "NewStr0ngPassword!"))

    assert user_repository.password_hash_calls == []


def test_change_password_raises_for_unknown_user():
    user_repository = FakeUserRepository(None)
    role_repository = FakeRoleRepository([])
    service = AuthService(user_repository, role_repository)

    with pytest.raises(UserNotFoundError):
        asyncio.run(
            service.change_password(uuid.uuid4(), "Str0ngPassword!", "NewStr0ngPassword!")
        )
