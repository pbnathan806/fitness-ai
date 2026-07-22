import uuid
from dataclasses import dataclass
from datetime import datetime

from core.constants import RoleName
from core.security import hash_password
from models.client import Client
from repositories.assignment_repository import AssignmentRepository
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


def _build_update_values(
    actor_id: uuid.UUID,
    first_name: str | None,
    last_name: str | None,
    phone_number: str | None,
    timezone: str | None,
) -> dict:
    values: dict = {"updated_by": actor_id}
    if first_name is not None:
        values["first_name"] = first_name
    if last_name is not None:
        values["last_name"] = last_name
    if phone_number is not None:
        values["phone_number"] = phone_number
    if timezone is not None:
        values["timezone"] = timezone
    return values


class ClientService:
    """Business logic for Client CRUD and its Version-1 RBAC rules (Task-14, Task-15.4).

    SUPER_ADMIN has full access, including `GET/PUT /clients/{id}` and
    `GET /clients`. TRAINER is READ-ONLY and scoped to clients it is assigned
    to via `client_trainer_assignments` (`GET /clients`, `GET /clients/{id}`).
    CLIENT may no longer use the `{id}` routes at all; it must use the
    self-service `GET/PUT /clients/me` routes, which resolve the profile from
    the caller's own `user_id` rather than an arbitrary path parameter.
    """

    def __init__(
        self,
        client_repository: ClientRepository,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        assignment_repository: AssignmentRepository,
    ) -> None:
        self._client_repository = client_repository
        self._user_repository = user_repository
        self._role_repository = role_repository
        self._assignment_repository = assignment_repository

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
        if actor_role == RoleName.SUPER_ADMIN:
            pass
        elif actor_role == RoleName.TRAINER:
            trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
            if trainer_id is None or not await self._client_repository.is_client_assigned_to_trainer(
                trainer_id, client_id
            ):
                raise ForbiddenError("You do not have permission to access this client profile.")
        else:
            raise ForbiddenError("You do not have permission to access this client profile.")

        record = await self._client_repository.get_by_id(client_id)
        if record is None:
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")
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
        if actor_role != RoleName.SUPER_ADMIN:
            raise ForbiddenError("Only Super Admins may update a client by id.")

        record = await self._client_repository.get_by_id(client_id)
        if record is None:
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")

        values = _build_update_values(actor_id, first_name, last_name, phone_number, timezone)
        updated = await self._client_repository.update(client_id, values)
        if updated is None:
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")
        return _to_profile(updated)

    async def list_clients(
        self, actor_role: str | None, actor_id: uuid.UUID, page: int, page_size: int
    ) -> PaginatedClients:
        offset = (page - 1) * page_size

        if actor_role == RoleName.SUPER_ADMIN:
            records, total = await self._client_repository.list_paginated(offset, page_size)
        elif actor_role == RoleName.TRAINER:
            trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
            if trainer_id is None:
                raise ForbiddenError("No trainer profile exists for the current user.")
            records, total = await self._client_repository.get_clients_for_trainer(
                trainer_id, offset, page_size
            )
        else:
            raise ForbiddenError("You do not have permission to list clients.")

        return PaginatedClients(
            items=[_to_profile(record) for record in records],
            page=page,
            page_size=page_size,
            total=total,
        )

    async def get_current_client(
        self, actor_role: str | None, actor_id: uuid.UUID
    ) -> ClientProfile:
        if actor_role != RoleName.CLIENT:
            raise ForbiddenError("Only Clients may access their own profile via /clients/me.")

        record = await self._client_repository.get_by_user_id(actor_id)
        if record is None:
            raise ClientNotFoundError("No client profile exists for the current user.")
        return _to_profile(record)

    async def update_current_client(
        self,
        actor_role: str | None,
        actor_id: uuid.UUID,
        first_name: str | None,
        last_name: str | None,
        phone_number: str | None,
        timezone: str | None,
    ) -> ClientProfile:
        if actor_role != RoleName.CLIENT:
            raise ForbiddenError("Only Clients may update their own profile via /clients/me.")

        record = await self._client_repository.get_by_user_id(actor_id)
        if record is None:
            raise ClientNotFoundError("No client profile exists for the current user.")

        values = _build_update_values(actor_id, first_name, last_name, phone_number, timezone)
        updated = await self._client_repository.update(record.client.id, values)
        if updated is None:
            raise ClientNotFoundError("No client profile exists for the current user.")
        return _to_profile(updated)
