import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.config import settings
from core.security import create_access_token, verify_password
from repositories.role_repository import RoleRepository
from repositories.user_repository import UserRepository


class InvalidCredentialsError(Exception):
    """Raised when login credentials do not match an active user."""


class RoleNotAssignedError(Exception):
    """Raised when a user attempts to select a role that is not assigned to them."""


@dataclass(frozen=True)
class AuthenticatedSession:
    access_token: str
    token_type: str
    expires_in: int
    user_id: uuid.UUID
    roles: list[str]


@dataclass(frozen=True)
class RoleSelection:
    access_token: str
    token_type: str
    expires_in: int
    active_role: str
    roles: list[str]


class AuthService:
    def __init__(self, user_repository: UserRepository, role_repository: RoleRepository) -> None:
        self._user_repository = user_repository
        self._role_repository = role_repository

    async def login(self, email: str, password: str) -> AuthenticatedSession:
        user = await self._user_repository.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password.")

        roles = await self._role_repository.get_role_names_for_user(user.id)

        await self._user_repository.update_last_login(user.id, datetime.now(timezone.utc))

        access_token = create_access_token(subject=str(user.id))
        return AuthenticatedSession(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user_id=user.id,
            roles=roles,
        )

    async def list_assigned_roles(self, user_id: uuid.UUID) -> list[str]:
        return await self._role_repository.get_role_names_for_user(user_id)

    async def switch_role(self, user_id: uuid.UUID, role: str) -> RoleSelection:
        roles = await self._role_repository.get_role_names_for_user(user_id)
        if role not in roles:
            raise RoleNotAssignedError(f"Role '{role}' is not assigned to this user.")

        access_token = create_access_token(subject=str(user_id), active_role=role)
        return RoleSelection(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            active_role=role,
            roles=roles,
        )
