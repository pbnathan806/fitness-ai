import asyncio
import uuid
from datetime import datetime, timezone

import pytest

from core.constants import RoleName
from core.security import hash_password, verify_password
from models.client import Client
from models.role import Role
from models.user import User
from repositories.client_repository import ClientRecord, ClientRepository
from repositories.role_repository import RoleRepository
from repositories.user_repository import UserRepository
from services.client_service import (
    ClientNotFoundError,
    ClientService,
    EmailAlreadyExistsError,
    ForbiddenError,
)


class FakeUserRepository(UserRepository):
    def __init__(self, users: list[User] | None = None) -> None:
        self._users: list[User] = list(users) if users else []
        self.created: list[User] = []

    async def get_by_email(self, email: str) -> User | None:
        for user in self._users:
            if user.email == email:
                return user
        return None

    async def update_last_login(self, user_id: uuid.UUID, login_time: datetime) -> None:
        raise NotImplementedError

    async def update_password_hash(self, user_id: uuid.UUID, password_hash: str) -> None:
        raise NotImplementedError

    async def create(self, email: str, password_hash: str) -> User:
        user = User(id=uuid.uuid4(), email=email, password_hash=password_hash)
        self._users.append(user)
        self.created.append(user)
        return user


class FakeRoleRepository(RoleRepository):
    def __init__(self) -> None:
        self._roles = {
            name: Role(id=uuid.uuid4(), name=name)
            for name in (RoleName.SUPER_ADMIN, RoleName.TRAINER, RoleName.CLIENT)
        }
        self.assignments: list[tuple[uuid.UUID, uuid.UUID]] = []

    async def get_role_names_for_user(self, user_id: uuid.UUID) -> list[str]:
        raise NotImplementedError

    async def get_by_name(self, name: str) -> Role | None:
        return self._roles.get(name)

    async def assign_role_to_user(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        self.assignments.append((user_id, role_id))


class FakeClientRepository(ClientRepository):
    def __init__(self) -> None:
        self._clients: dict[uuid.UUID, Client] = {}
        self._emails: dict[uuid.UUID, str] = {}

    def seed(self, client: Client, email: str) -> None:
        self._clients[client.id] = client
        self._emails[client.id] = email

    async def create(self, client: Client) -> Client:
        now = datetime.now(timezone.utc)
        client.id = client.id or uuid.uuid4()
        client.created_at = now
        client.updated_at = now
        self._clients[client.id] = client
        return client

    async def get_by_id(self, client_id: uuid.UUID) -> ClientRecord | None:
        client = self._clients.get(client_id)
        if client is None:
            return None
        return ClientRecord(client=client, email=self._emails.get(client_id, ""))

    async def get_by_user_id(self, user_id: uuid.UUID) -> ClientRecord | None:
        for client in self._clients.values():
            if client.user_id == user_id:
                return ClientRecord(client=client, email=self._emails.get(client.id, ""))
        return None

    async def update(self, client_id: uuid.UUID, values: dict) -> ClientRecord | None:
        client = self._clients.get(client_id)
        if client is None:
            return None
        for key, value in values.items():
            setattr(client, key, value)
        return ClientRecord(client=client, email=self._emails.get(client_id, ""))

    async def list_paginated(self, offset: int, limit: int) -> tuple[list[ClientRecord], int]:
        ordered = sorted(self._clients.values(), key=lambda c: c.created_at, reverse=True)
        page = ordered[offset : offset + limit]
        records = [ClientRecord(client=c, email=self._emails.get(c.id, "")) for c in page]
        return records, len(ordered)


def _make_client(user_id: uuid.UUID, **overrides) -> Client:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid.uuid4(),
        user_id=user_id,
        first_name="Jane",
        last_name="Doe",
        phone_number="+1-555-0100",
        timezone="America/New_York",
        created_by=uuid.uuid4(),
        updated_by=uuid.uuid4(),
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return Client(**defaults)


def _make_service() -> tuple[ClientService, FakeClientRepository, FakeUserRepository, FakeRoleRepository]:
    client_repository = FakeClientRepository()
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    service = ClientService(client_repository, user_repository, role_repository)
    return service, client_repository, user_repository, role_repository


def test_create_client_succeeds_for_super_admin():
    service, client_repository, user_repository, role_repository = _make_service()
    actor_id = uuid.uuid4()

    profile = asyncio.run(
        service.create_client(
            actor_role=RoleName.SUPER_ADMIN,
            actor_id=actor_id,
            email="client@example.com",
            password="Str0ngPassword!",
            first_name="Jane",
            last_name="Doe",
            phone_number="+1-555-0100",
            timezone="America/New_York",
        )
    )

    assert profile.email == "client@example.com"
    assert profile.first_name == "Jane"
    assert len(user_repository.created) == 1
    created_user = user_repository.created[0]
    assert verify_password("Str0ngPassword!", created_user.password_hash)
    assert len(role_repository.assignments) == 1
    assigned_user_id, assigned_role_id = role_repository.assignments[0]
    assert assigned_user_id == created_user.id
    assert assigned_role_id == role_repository._roles[RoleName.CLIENT].id


def test_create_client_rejects_non_super_admin():
    service, *_ = _make_service()

    for role in (RoleName.CLIENT, RoleName.TRAINER, None):
        with pytest.raises(ForbiddenError):
            asyncio.run(
                service.create_client(
                    actor_role=role,
                    actor_id=uuid.uuid4(),
                    email="client@example.com",
                    password="Str0ngPassword!",
                    first_name="Jane",
                    last_name="Doe",
                    phone_number=None,
                    timezone="America/New_York",
                )
            )


def test_create_client_rejects_duplicate_email():
    service, client_repository, user_repository, role_repository = _make_service()
    asyncio.run(user_repository.create(email="client@example.com", password_hash=hash_password("Str0ngPassword!")))

    with pytest.raises(EmailAlreadyExistsError):
        asyncio.run(
            service.create_client(
                actor_role=RoleName.SUPER_ADMIN,
                actor_id=uuid.uuid4(),
                email="client@example.com",
                password="Str0ngPassword!",
                first_name="Jane",
                last_name="Doe",
                phone_number=None,
                timezone="America/New_York",
            )
        )


def test_get_client_succeeds_for_super_admin():
    service, client_repository, *_ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")

    profile = asyncio.run(
        service.get_client(actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), client_id=client.id)
    )

    assert profile.id == client.id
    assert profile.email == "client@example.com"


def test_get_client_succeeds_for_owning_client():
    service, client_repository, *_ = _make_service()
    user_id = uuid.uuid4()
    client = _make_client(user_id=user_id)
    client_repository.seed(client, "client@example.com")

    profile = asyncio.run(
        service.get_client(actor_role=RoleName.CLIENT, actor_id=user_id, client_id=client.id)
    )

    assert profile.id == client.id


def test_get_client_rejects_other_client():
    service, client_repository, *_ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_client(actor_role=RoleName.CLIENT, actor_id=uuid.uuid4(), client_id=client.id)
        )


def test_get_client_rejects_trainer():
    service, client_repository, *_ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_client(actor_role=RoleName.TRAINER, actor_id=uuid.uuid4(), client_id=client.id)
        )


def test_get_client_raises_not_found_for_missing_client():
    service, *_ = _make_service()

    with pytest.raises(ClientNotFoundError):
        asyncio.run(
            service.get_client(actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4(), client_id=uuid.uuid4())
        )


def test_update_client_applies_only_provided_fields():
    service, client_repository, *_ = _make_service()
    user_id = uuid.uuid4()
    client = _make_client(user_id=user_id, first_name="Jane", last_name="Doe")
    client_repository.seed(client, "client@example.com")

    profile = asyncio.run(
        service.update_client(
            actor_role=RoleName.CLIENT,
            actor_id=user_id,
            client_id=client.id,
            first_name="Janet",
            last_name=None,
            phone_number=None,
            timezone=None,
        )
    )

    assert profile.first_name == "Janet"
    assert profile.last_name == "Doe"


def test_update_client_rejects_other_client():
    service, client_repository, *_ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.update_client(
                actor_role=RoleName.CLIENT,
                actor_id=uuid.uuid4(),
                client_id=client.id,
                first_name="Hacker",
                last_name=None,
                phone_number=None,
                timezone=None,
            )
        )


def test_list_clients_succeeds_for_super_admin_with_pagination():
    service, client_repository, *_ = _make_service()
    for _ in range(5):
        client_repository.seed(_make_client(user_id=uuid.uuid4()), "client@example.com")

    result = asyncio.run(service.list_clients(actor_role=RoleName.SUPER_ADMIN, page=1, page_size=2))

    assert result.total == 5
    assert len(result.items) == 2
    assert result.page == 1
    assert result.page_size == 2


def test_list_clients_rejects_client_role():
    service, *_ = _make_service()

    with pytest.raises(ForbiddenError):
        asyncio.run(service.list_clients(actor_role=RoleName.CLIENT, page=1, page_size=20))


def test_list_clients_rejects_trainer_role():
    service, *_ = _make_service()

    with pytest.raises(ForbiddenError):
        asyncio.run(service.list_clients(actor_role=RoleName.TRAINER, page=1, page_size=20))
