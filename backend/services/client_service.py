import uuid
from dataclasses import dataclass
from datetime import datetime

from core.constants import RoleName
from core.security import hash_password
from models.client import Client
from repositories.client_repository import ClientRecord, ClientRepository
from repositories.role_repository import RoleRepository
from repositories.user_repository import UserRepository


class EmailAlreadyExistsError(Exception):
    """Raised when attempting to create a client for an email already in use."""


class ClientNotFoundError(Exception):
    """Raised when no client profile exists for the requested identifier."""


class ForbiddenError(Exception):
    """Raised when the acting user's role does not permit the requested action."""


@dataclass(frozen=True)
class ClientProfile:
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    phone_number: str | None
    timezone: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PaginatedClients:
    items: list[ClientProfile]
    page: int
    page_size: int
    total: int


def _to_profile(record: ClientRecord) -> ClientProfile:
    client = record.client
    return ClientProfile(
        id=client.id,
        user_id=client.user_id,
        email=record.email,
        first_name=client.first_name,
        last_name=client.last_name,
        phone_number=client.phone_number,
        timezone=client.timezone,
        created_at=client.created_at,
        updated_at=client.updated_at,
    )


class ClientService:
    """Business logic for Client CRUD and its Version-1 RBAC rules (Task-14).

    SUPER_ADMIN has full access. CLIENT may only read/update its own profile
    (matched via the caller's user_id against `clients.user_id`). Any other
    role (including TRAINER, whose access arrives in Task-15) is rejected.
    """

    def __init__(
        self,
        client_repository: ClientRepository,
        user_repository: UserRepository,
        role_repository: RoleRepository,
    ) -> None:
        self._client_repository = client_repository
        self._user_repository = user_repository
        self._role_repository = role_repository

    async def create_client(
        self,
        actor_role: str | None,
        actor_id: uuid.UUID,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone_number: str | None,
        timezone: str,
    ) -> ClientProfile:
        if actor_role != RoleName.SUPER_ADMIN:
            raise ForbiddenError("Only Super Admins may create clients.")

        existing_user = await self._user_repository.get_by_email(email)
        if existing_user is not None:
            raise EmailAlreadyExistsError(f"A user with email '{email}' already exists.")

        client_role = await self._role_repository.get_by_name(RoleName.CLIENT)
        if client_role is None:
            raise RuntimeError("CLIENT role is not seeded in the database.")

        user = await self._user_repository.create(
            email=email, password_hash=hash_password(password)
        )
        await self._role_repository.assign_role_to_user(user.id, client_role.id)

        client = await self._client_repository.create(
            Client(
                user_id=user.id,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                timezone=timezone,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
        return ClientProfile(
            id=client.id,
            user_id=client.user_id,
            email=user.email,
            first_name=client.first_name,
            last_name=client.last_name,
            phone_number=client.phone_number,
            timezone=client.timezone,
            created_at=client.created_at,
            updated_at=client.updated_at,
        )

    async def get_client(
        self, actor_role: str | None, actor_id: uuid.UUID, client_id: uuid.UUID
    ) -> ClientProfile:
        record = await self._client_repository.get_by_id(client_id)
        if record is None:
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")

        self._authorize_profile_access(actor_role, actor_id, record)
        return _to_profile(record)

    async def update_client(
        self,
        actor_role: str | None,
        actor_id: uuid.UUID,
        client_id: uuid.UUID,
        first_name: str | None,
        last_name: str | None,
        phone_number: str | None,
        timezone: str | None,
    ) -> ClientProfile:
        record = await self._client_repository.get_by_id(client_id)
        if record is None:
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")

        self._authorize_profile_access(actor_role, actor_id, record)

        values: dict = {"updated_by": actor_id}
        if first_name is not None:
            values["first_name"] = first_name
        if last_name is not None:
            values["last_name"] = last_name
        if phone_number is not None:
            values["phone_number"] = phone_number
        if timezone is not None:
            values["timezone"] = timezone

        updated = await self._client_repository.update(client_id, values)
        if updated is None:
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")
        return _to_profile(updated)

    async def list_clients(
        self, actor_role: str | None, page: int, page_size: int
    ) -> PaginatedClients:
        if actor_role != RoleName.SUPER_ADMIN:
            raise ForbiddenError("Only Super Admins may list clients.")

        offset = (page - 1) * page_size
        records, total = await self._client_repository.list_paginated(offset, page_size)
        return PaginatedClients(
            items=[_to_profile(record) for record in records],
            page=page,
            page_size=page_size,
            total=total,
        )

    @staticmethod
    def _authorize_profile_access(
        actor_role: str | None, actor_id: uuid.UUID, record: ClientRecord
    ) -> None:
        if actor_role == RoleName.SUPER_ADMIN:
            return
        if actor_role == RoleName.CLIENT and record.client.user_id == actor_id:
            return
        raise ForbiddenError("You do not have permission to access this client profile.")
