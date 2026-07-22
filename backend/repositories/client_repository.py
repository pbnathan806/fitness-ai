import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.client import Client
from models.client_trainer_assignment import ClientTrainerAssignment
from models.user import User


@dataclass(frozen=True)
class ClientRecord:
    """A client profile joined with its account email.

    Email lives on `users`, not `clients`, so reads join both tables rather
    than requiring callers to make a second round trip through
    UserRepository for every client returned (including list pages).
    """

    client: Client
    email: str


class ClientRepository(ABC):
    """Abstraction over client profile persistence, decoupling callers from SQLAlchemy."""

    @abstractmethod
    async def create(self, client: Client) -> Client: ...

    @abstractmethod
    async def get_by_id(self, client_id: uuid.UUID) -> ClientRecord | None: ...

    @abstractmethod
    async def get_by_user_id(self, user_id: uuid.UUID) -> ClientRecord | None: ...

    @abstractmethod
    async def update(self, client_id: uuid.UUID, values: dict) -> ClientRecord | None: ...

    @abstractmethod
    async def list_paginated(
        self, offset: int, limit: int
    ) -> tuple[list[ClientRecord], int]: ...

    @abstractmethod
    async def get_clients_for_trainer(
        self, trainer_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[ClientRecord], int]: ...

    @abstractmethod
    async def is_client_assigned_to_trainer(
        self, trainer_id: uuid.UUID, client_id: uuid.UUID
    ) -> bool: ...


class SQLAlchemyClientRepository(ClientRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, client: Client) -> Client:
        self._session.add(client)
        await self._session.commit()
        await self._session.refresh(client)
        return client

    async def get_by_id(self, client_id: uuid.UUID) -> ClientRecord | None:
        result = await self._session.execute(
            select(Client, User.email)
            .join(User, User.id == Client.user_id)
            .where(Client.id == client_id)
        )
        row = result.first()
        if row is None:
            return None
        client, email = row
        return ClientRecord(client=client, email=email)

    async def get_by_user_id(self, user_id: uuid.UUID) -> ClientRecord | None:
        result = await self._session.execute(
            select(Client, User.email)
            .join(User, User.id == Client.user_id)
            .where(Client.user_id == user_id)
        )
        row = result.first()
        if row is None:
            return None
        client, email = row
        return ClientRecord(client=client, email=email)

    async def update(self, client_id: uuid.UUID, values: dict) -> ClientRecord | None:
        if values:
            await self._session.execute(
                update(Client).where(Client.id == client_id).values(**values)
            )
            await self._session.commit()
        return await self.get_by_id(client_id)

    async def list_paginated(
        self, offset: int, limit: int
    ) -> tuple[list[ClientRecord], int]:
        total_result = await self._session.execute(select(func.count()).select_from(Client))
        total = total_result.scalar_one()

        result = await self._session.execute(
            select(Client, User.email)
            .join(User, User.id == Client.user_id)
            .order_by(Client.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        records = [ClientRecord(client=client, email=email) for client, email in result.all()]
        return records, total

    async def get_clients_for_trainer(
        self, trainer_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[ClientRecord], int]:
        total_result = await self._session.execute(
            select(func.count())
            .select_from(ClientTrainerAssignment)
            .where(ClientTrainerAssignment.trainer_id == trainer_id)
        )
        total = total_result.scalar_one()

        result = await self._session.execute(
            select(Client, User.email)
            .join(User, User.id == Client.user_id)
            .join(
                ClientTrainerAssignment,
                ClientTrainerAssignment.client_id == Client.id,
            )
            .where(ClientTrainerAssignment.trainer_id == trainer_id)
            .order_by(Client.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        records = [ClientRecord(client=client, email=email) for client, email in result.all()]
        return records, total

    async def is_client_assigned_to_trainer(
        self, trainer_id: uuid.UUID, client_id: uuid.UUID
    ) -> bool:
        result = await self._session.execute(
            select(ClientTrainerAssignment.id).where(
                ClientTrainerAssignment.trainer_id == trainer_id,
                ClientTrainerAssignment.client_id == client_id,
            )
        )
        return result.scalar_one_or_none() is not None
