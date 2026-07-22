import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.client import Client
from models.client_trainer_assignment import ClientTrainerAssignment
from models.trainer_profile import TrainerProfile
from models.user import User


@dataclass(frozen=True)
class AssignedClientRecord:
    """A client assigned to a trainer, joined with the assignment and the client's account email."""

    assignment: ClientTrainerAssignment
    client: Client
    email: str


@dataclass(frozen=True)
class AssignedTrainerRecord:
    """A trainer assigned to a client, joined with the assignment and the trainer's account email."""

    assignment: ClientTrainerAssignment
    trainer: TrainerProfile
    email: str


class AssignmentRepository(ABC):
    """Abstraction over client-trainer assignment persistence, decoupling callers from SQLAlchemy."""

    @abstractmethod
    async def client_exists(self, client_id: uuid.UUID) -> bool: ...

    @abstractmethod
    async def trainer_exists(self, trainer_id: uuid.UUID) -> bool: ...

    @abstractmethod
    async def exists_for_pair(self, client_id: uuid.UUID, trainer_id: uuid.UUID) -> bool: ...

    @abstractmethod
    async def client_has_primary_trainer(self, client_id: uuid.UUID) -> bool: ...

    @abstractmethod
    async def create(
        self, assignment: ClientTrainerAssignment
    ) -> ClientTrainerAssignment: ...

    @abstractmethod
    async def get_by_id(
        self, assignment_id: uuid.UUID
    ) -> ClientTrainerAssignment | None: ...

    @abstractmethod
    async def delete(self, assignment_id: uuid.UUID) -> bool: ...

    @abstractmethod
    async def list_paginated(
        self, offset: int, limit: int
    ) -> tuple[list[ClientTrainerAssignment], int]: ...

    @abstractmethod
    async def get_trainer_id_by_user_id(self, user_id: uuid.UUID) -> uuid.UUID | None: ...

    @abstractmethod
    async def list_clients_for_trainer(
        self, trainer_id: uuid.UUID
    ) -> list[AssignedClientRecord]: ...

    @abstractmethod
    async def list_trainers_for_client(
        self, client_id: uuid.UUID
    ) -> list[AssignedTrainerRecord]: ...


class SQLAlchemyAssignmentRepository(AssignmentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def client_exists(self, client_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(Client.id).where(Client.id == client_id)
        )
        return result.scalar_one_or_none() is not None

    async def trainer_exists(self, trainer_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(TrainerProfile.id).where(TrainerProfile.id == trainer_id)
        )
        return result.scalar_one_or_none() is not None

    async def exists_for_pair(self, client_id: uuid.UUID, trainer_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(ClientTrainerAssignment.id).where(
                ClientTrainerAssignment.client_id == client_id,
                ClientTrainerAssignment.trainer_id == trainer_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def client_has_primary_trainer(self, client_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(ClientTrainerAssignment.id).where(
                ClientTrainerAssignment.client_id == client_id,
                ClientTrainerAssignment.is_primary.is_(True),
            )
        )
        return result.scalar_one_or_none() is not None

    async def create(
        self, assignment: ClientTrainerAssignment
    ) -> ClientTrainerAssignment:
        self._session.add(assignment)
        await self._session.commit()
        await self._session.refresh(assignment)
        return assignment

    async def get_by_id(
        self, assignment_id: uuid.UUID
    ) -> ClientTrainerAssignment | None:
        result = await self._session.execute(
            select(ClientTrainerAssignment).where(
                ClientTrainerAssignment.id == assignment_id
            )
        )
        return result.scalar_one_or_none()

    async def delete(self, assignment_id: uuid.UUID) -> bool:
        assignment = await self.get_by_id(assignment_id)
        if assignment is None:
            return False
        await self._session.delete(assignment)
        await self._session.commit()
        return True

    async def list_paginated(
        self, offset: int, limit: int
    ) -> tuple[list[ClientTrainerAssignment], int]:
        total_result = await self._session.execute(
            select(func.count()).select_from(ClientTrainerAssignment)
        )
        total = total_result.scalar_one()

        result = await self._session.execute(
            select(ClientTrainerAssignment)
            .order_by(ClientTrainerAssignment.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_trainer_id_by_user_id(self, user_id: uuid.UUID) -> uuid.UUID | None:
        result = await self._session.execute(
            select(TrainerProfile.id).where(TrainerProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_clients_for_trainer(
        self, trainer_id: uuid.UUID
    ) -> list[AssignedClientRecord]:
        result = await self._session.execute(
            select(ClientTrainerAssignment, Client, User.email)
            .join(Client, Client.id == ClientTrainerAssignment.client_id)
            .join(User, User.id == Client.user_id)
            .where(ClientTrainerAssignment.trainer_id == trainer_id)
            .order_by(ClientTrainerAssignment.assigned_at.desc())
        )
        return [
            AssignedClientRecord(assignment=assignment, client=client, email=email)
            for assignment, client, email in result.all()
        ]

    async def list_trainers_for_client(
        self, client_id: uuid.UUID
    ) -> list[AssignedTrainerRecord]:
        result = await self._session.execute(
            select(ClientTrainerAssignment, TrainerProfile, User.email)
            .join(TrainerProfile, TrainerProfile.id == ClientTrainerAssignment.trainer_id)
            .join(User, User.id == TrainerProfile.user_id)
            .where(ClientTrainerAssignment.client_id == client_id)
            .order_by(ClientTrainerAssignment.assigned_at.desc())
        )
        return [
            AssignedTrainerRecord(assignment=assignment, trainer=trainer, email=email)
            for assignment, trainer, email in result.all()
        ]
