import uuid
from abc import ABC, abstractmethod
from datetime import time

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.trainer_availability import TrainerAvailability


class TrainerAvailabilityRepository(ABC):
    """Abstraction over trainer availability persistence, decoupling callers from SQLAlchemy."""

    @abstractmethod
    async def create(self, availability: TrainerAvailability) -> TrainerAvailability: ...

    @abstractmethod
    async def get_by_id(self, availability_id: uuid.UUID) -> TrainerAvailability | None: ...

    @abstractmethod
    async def list_for_trainer(self, trainer_id: uuid.UUID) -> list[TrainerAvailability]: ...

    @abstractmethod
    async def update(
        self, availability_id: uuid.UUID, values: dict
    ) -> TrainerAvailability | None: ...

    @abstractmethod
    async def delete(self, availability_id: uuid.UUID) -> bool: ...

    @abstractmethod
    async def find_overlapping(
        self,
        trainer_id: uuid.UUID,
        weekday: int,
        start_time: time,
        end_time: time,
        exclude_id: uuid.UUID | None = None,
    ) -> TrainerAvailability | None: ...


class SQLAlchemyTrainerAvailabilityRepository(TrainerAvailabilityRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, availability: TrainerAvailability) -> TrainerAvailability:
        self._session.add(availability)
        await self._session.commit()
        await self._session.refresh(availability)
        return availability

    async def get_by_id(self, availability_id: uuid.UUID) -> TrainerAvailability | None:
        result = await self._session.execute(
            select(TrainerAvailability).where(TrainerAvailability.id == availability_id)
        )
        return result.scalar_one_or_none()

    async def list_for_trainer(self, trainer_id: uuid.UUID) -> list[TrainerAvailability]:
        result = await self._session.execute(
            select(TrainerAvailability)
            .where(TrainerAvailability.trainer_id == trainer_id)
            .order_by(TrainerAvailability.weekday, TrainerAvailability.start_time)
        )
        return list(result.scalars().all())

    async def update(
        self, availability_id: uuid.UUID, values: dict
    ) -> TrainerAvailability | None:
        if values:
            await self._session.execute(
                update(TrainerAvailability)
                .where(TrainerAvailability.id == availability_id)
                .values(**values)
            )
            await self._session.commit()
        return await self.get_by_id(availability_id)

    async def delete(self, availability_id: uuid.UUID) -> bool:
        availability = await self.get_by_id(availability_id)
        if availability is None:
            return False
        await self._session.delete(availability)
        await self._session.commit()
        return True

    async def find_overlapping(
        self,
        trainer_id: uuid.UUID,
        weekday: int,
        start_time: time,
        end_time: time,
        exclude_id: uuid.UUID | None = None,
    ) -> TrainerAvailability | None:
        conditions = [
            TrainerAvailability.trainer_id == trainer_id,
            TrainerAvailability.weekday == weekday,
            TrainerAvailability.start_time < end_time,
            TrainerAvailability.end_time > start_time,
        ]
        if exclude_id is not None:
            conditions.append(TrainerAvailability.id != exclude_id)

        result = await self._session.execute(
            select(TrainerAvailability).where(*conditions)
        )
        return result.scalars().first()
