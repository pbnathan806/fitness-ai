import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from core.security import hash_password, verify_password
from models.password_reset_token import PasswordResetToken
from models.user import User
from repositories.password_reset_token_repository import PasswordResetTokenRepository
from repositories.user_repository import UserRepository
from services.password_reset_service import (
    InvalidResetTokenError,
    PasswordResetNotifier,
    PasswordResetService,
)


class FakeUserRepository(UserRepository):
    def __init__(self, user: User | None) -> None:
        self._user = user
        self.password_hash_calls: list[tuple[uuid.UUID, str]] = []

    async def get_by_email(self, email: str) -> User | None:
        if self._user is not None and self._user.email == email:
            return self._user
        return None

    async def update_last_login(self, user_id: uuid.UUID, login_time: datetime) -> None:
        raise NotImplementedError

    async def update_password_hash(self, user_id: uuid.UUID, password_hash: str) -> None:
        self.password_hash_calls.append((user_id, password_hash))
        if self._user is not None and self._user.id == user_id:
            self._user.password_hash = password_hash

    async def create(self, email: str, password_hash: str) -> User:
        raise NotImplementedError


class FakePasswordResetTokenRepository(PasswordResetTokenRepository):
    def __init__(self) -> None:
        self._tokens: dict[uuid.UUID, PasswordResetToken] = {}
        self.invalidate_calls: list[uuid.UUID] = []

    async def create(
        self, user_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> PasswordResetToken:
        token = PasswordResetToken(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._tokens[token.id] = token
        return token

    async def get_valid_by_token_hash(
        self, token_hash: str, now: datetime
    ) -> PasswordResetToken | None:
        for token in self._tokens.values():
            if (
                token.token_hash == token_hash
                and token.used_at is None
                and token.expires_at > now
            ):
                return token
        return None

    async def mark_used(self, token_id: uuid.UUID, used_at: datetime) -> None:
        if token_id in self._tokens:
            self._tokens[token_id].used_at = used_at

    async def invalidate_active_tokens_for_user(
        self, user_id: uuid.UUID, used_at: datetime
    ) -> None:
        self.invalidate_calls.append(user_id)
        for token in self._tokens.values():
            if token.user_id == user_id and token.used_at is None:
                token.used_at = used_at


class FakePasswordResetNotifier(PasswordResetNotifier):
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send_reset_link(self, email: str, raw_token: str) -> None:
        self.sent.append((email, raw_token))


def _make_user(email: str, password: str) -> User:
    return User(id=uuid.uuid4(), email=email, password_hash=hash_password(password))


def test_request_password_reset_creates_token_and_notifies_for_known_email():
    user = _make_user("trainer@example.com", "Str0ngPassword!")
    user_repository = FakeUserRepository(user)
    token_repository = FakePasswordResetTokenRepository()
    notifier = FakePasswordResetNotifier()
    service = PasswordResetService(user_repository, token_repository, notifier)

    asyncio.run(service.request_password_reset("trainer@example.com"))

    assert len(notifier.sent) == 1
    sent_email, raw_token = notifier.sent[0]
    assert sent_email == "trainer@example.com"
    assert raw_token


def test_request_password_reset_does_not_notify_for_unknown_email():
    user_repository = FakeUserRepository(None)
    token_repository = FakePasswordResetTokenRepository()
    notifier = FakePasswordResetNotifier()
    service = PasswordResetService(user_repository, token_repository, notifier)

    asyncio.run(service.request_password_reset("missing@example.com"))

    assert notifier.sent == []


def test_request_password_reset_invalidates_prior_active_tokens():
    user = _make_user("trainer@example.com", "Str0ngPassword!")
    user_repository = FakeUserRepository(user)
    token_repository = FakePasswordResetTokenRepository()
    notifier = FakePasswordResetNotifier()
    service = PasswordResetService(user_repository, token_repository, notifier)

    asyncio.run(service.request_password_reset("trainer@example.com"))
    asyncio.run(service.request_password_reset("trainer@example.com"))

    assert token_repository.invalidate_calls == [user.id, user.id]


def test_reset_password_updates_password_hash_for_valid_token():
    user = _make_user("trainer@example.com", "Str0ngPassword!")
    user_repository = FakeUserRepository(user)
    token_repository = FakePasswordResetTokenRepository()
    notifier = FakePasswordResetNotifier()
    service = PasswordResetService(user_repository, token_repository, notifier)

    asyncio.run(service.request_password_reset("trainer@example.com"))
    _, raw_token = notifier.sent[0]

    asyncio.run(service.reset_password(raw_token, "NewStr0ngPassword!"))

    assert len(user_repository.password_hash_calls) == 1
    assert verify_password("NewStr0ngPassword!", user.password_hash)


def test_reset_password_rejects_unknown_token():
    user_repository = FakeUserRepository(None)
    token_repository = FakePasswordResetTokenRepository()
    notifier = FakePasswordResetNotifier()
    service = PasswordResetService(user_repository, token_repository, notifier)

    with pytest.raises(InvalidResetTokenError):
        asyncio.run(service.reset_password("not-a-real-token", "NewStr0ngPassword!"))


def test_reset_password_rejects_expired_token():
    user = _make_user("trainer@example.com", "Str0ngPassword!")
    user_repository = FakeUserRepository(user)
    token_repository = FakePasswordResetTokenRepository()
    notifier = FakePasswordResetNotifier()
    service = PasswordResetService(user_repository, token_repository, notifier)

    asyncio.run(service.request_password_reset("trainer@example.com"))
    _, raw_token = notifier.sent[0]
    for token in token_repository._tokens.values():
        token.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    with pytest.raises(InvalidResetTokenError):
        asyncio.run(service.reset_password(raw_token, "NewStr0ngPassword!"))


def test_reset_password_rejects_already_used_token():
    user = _make_user("trainer@example.com", "Str0ngPassword!")
    user_repository = FakeUserRepository(user)
    token_repository = FakePasswordResetTokenRepository()
    notifier = FakePasswordResetNotifier()
    service = PasswordResetService(user_repository, token_repository, notifier)

    asyncio.run(service.request_password_reset("trainer@example.com"))
    _, raw_token = notifier.sent[0]

    asyncio.run(service.reset_password(raw_token, "NewStr0ngPassword!"))

    with pytest.raises(InvalidResetTokenError):
        asyncio.run(service.reset_password(raw_token, "AnotherStr0ngPassword!"))
