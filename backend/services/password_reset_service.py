import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

from core.config import settings
from core.security import generate_password_reset_token, hash_password, hash_reset_token
from repositories.password_reset_token_repository import PasswordResetTokenRepository
from repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class InvalidResetTokenError(Exception):
    """Raised when a password reset token is missing, expired, or already used."""


class PasswordResetNotifier(ABC):
    """Delivery port for password reset links.

    Real delivery (email) belongs to the Notifications module (Phase 8 of
    IMPLEMENTATION_PLAN.md) and is intentionally out of scope for Task-11.
    This abstraction lets that module plug in a real sender later without
    changing PasswordResetService (Dependency Inversion).
    """

    @abstractmethod
    async def send_reset_link(self, email: str, raw_token: str) -> None: ...


class ConsolePasswordResetNotifier(PasswordResetNotifier):
    """DEV-ONLY stand-in for the future email notifier.

    Prints the raw reset token to the local server console instead of
    emailing it, so the Forgot Password flow can be exercised locally
    without a real (paid/unapproved) email provider. Must be replaced by a
    real notifier when the Notifications module is implemented; never wire
    this into a deployed environment.
    """

    async def send_reset_link(self, email: str, raw_token: str) -> None:
        print(f"[DEV] Password reset requested for {email}. Reset token: {raw_token}")


class PasswordResetService:
    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: PasswordResetTokenRepository,
        notifier: PasswordResetNotifier,
    ) -> None:
        self._user_repository = user_repository
        self._token_repository = token_repository
        self._notifier = notifier

    async def request_password_reset(self, email: str) -> None:
        """Issue a reset token if `email` belongs to a registered user.

        Always completes without raising and without revealing whether the
        email is registered, to prevent account enumeration.
        """
        user = await self._user_repository.get_by_email(email)
        if user is None:
            logger.info("Password reset requested for an unregistered email.")
            return

        now = datetime.now(timezone.utc)
        await self._token_repository.invalidate_active_tokens_for_user(user.id, now)

        raw_token = generate_password_reset_token()
        token_hash = hash_reset_token(raw_token)
        expires_at = now + timedelta(minutes=settings.password_reset_token_expire_minutes)
        await self._token_repository.create(user.id, token_hash, expires_at)

        logger.info("Password reset token issued for user_id=%s", user.id)
        await self._notifier.send_reset_link(user.email, raw_token)

    async def reset_password(self, raw_token: str, new_password: str) -> None:
        """Consume a reset token and set a new password hash for its owner."""
        token_hash = hash_reset_token(raw_token)
        now = datetime.now(timezone.utc)

        token = await self._token_repository.get_valid_by_token_hash(token_hash, now)
        if token is None:
            raise InvalidResetTokenError("Reset token is invalid or has expired.")

        new_password_hash = hash_password(new_password)
        await self._user_repository.update_password_hash(token.user_id, new_password_hash)
        await self._token_repository.invalidate_active_tokens_for_user(token.user_id, now)

        logger.info("Password reset completed for user_id=%s", token.user_id)
