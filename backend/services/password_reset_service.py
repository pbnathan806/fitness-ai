import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

import resend

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


_RESET_EMAIL_SUBJECT = "Reset your Fitness AI Platform password"

_RESET_EMAIL_TEXT_TEMPLATE = """\
Hi,

We received a request to reset your Fitness AI Platform password.

Reset your password using the link below:
{reset_url}

This link expires in {expire_minutes} minutes. If you didn't request this, \
you can safely ignore this email - your password will not be changed.
"""

_RESET_EMAIL_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
  <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f4f4f5; margin: 0; padding: 32px 16px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td align="center">
          <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; padding: 32px;">
            <tr>
              <td>
                <h1 style="font-size: 18px; margin: 0 0 16px; color: #18181b;">Reset your password</h1>
                <p style="font-size: 14px; color: #3f3f46; line-height: 1.5; margin: 0 0 24px;">
                  We received a request to reset your Fitness AI Platform password. Click the button below to choose a new one.
                </p>
                <table role="presentation" cellpadding="0" cellspacing="0">
                  <tr>
                    <td style="border-radius: 6px; background-color: #18181b;">
                      <a href="{reset_url}" style="display: inline-block; padding: 10px 20px; font-size: 14px; color: #ffffff; text-decoration: none; font-weight: 500;">
                        Reset Password
                      </a>
                    </td>
                  </tr>
                </table>
                <p style="font-size: 12px; color: #71717a; line-height: 1.5; margin: 24px 0 0;">
                  This link expires in {expire_minutes} minutes. If you didn't request this, you can safely ignore this email - your password will not be changed.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


class ResendPasswordResetNotifier(PasswordResetNotifier):
    """Production email delivery via Resend.

    Only wired in when `settings.is_production` (see
    routers/auth.py::get_password_reset_notifier); local/dev environments
    use ConsolePasswordResetNotifier instead, so a Resend account is never
    required to run this app locally.
    """

    def __init__(self, api_key: str, from_email: str, frontend_base_url: str) -> None:
        resend.api_key = api_key
        self._from_email = from_email
        self._frontend_base_url = frontend_base_url

    async def send_reset_link(self, email: str, raw_token: str) -> None:
        reset_url = f"{self._frontend_base_url}/reset-password?token={raw_token}"
        expire_minutes = settings.password_reset_token_expire_minutes

        params: resend.Emails.SendParams = {
            "from": self._from_email,
            "to": [email],
            "subject": _RESET_EMAIL_SUBJECT,
            "html": _RESET_EMAIL_HTML_TEMPLATE.format(reset_url=reset_url, expire_minutes=expire_minutes),
            "text": _RESET_EMAIL_TEXT_TEMPLATE.format(reset_url=reset_url, expire_minutes=expire_minutes),
        }
        # resend.Emails.send is a blocking network call; run it off the
        # event loop so a slow/hung request to Resend can't stall other
        # requests being served by this async process.
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info("Password reset email sent via Resend.")


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
