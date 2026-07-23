import uuid
from abc import ABC, abstractmethod

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.measurement import Measurement


class MeasurementRepository(ABC):
    """Abstraction over measurement persistence, decoupling callers from SQLAlchemy.

    Deliberately has no update()/delete() method: measurements are immutable
    and historical records are always preserved.
    """

    @abstractmethod
    async def create(self, measurement: Measurement) -> Measurement: ...

    @abstractmethod
    async def get_by_id(self, measurement_id: uuid.UUID) -> Measurement | None: ...

    @abstractmethod
    async def list_paginated(self, offset: int, limit: int) -> tuple[list[Measurement], int]: ...

    @abstractmethod
    async def list_for_client(
        self, client_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[Measurement], int]: ...

    @abstractmethod
    async def list_for_clients(
        self, client_ids: list[uuid.UUID], offset: int, limit: int
    ) -> tuple[list[Measurement], int]: ...

    @abstractmethod
    async def list_all_for_client(self, client_id: uuid.UUID) -> list[Measurement]: ...


class SQLAlchemyMeasurementRepository(MeasurementRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, measurement: Measurement) -> Measurement:
        self._session.add(measurement)
        await self._session.commit()
        await self._session.refresh(measurement)
        return measurement

    async def get_by_id(self, measurement_id: uuid.UUID) -> Measurement | None:
        result = await self._session.execute(
            select(Measurement).where(Measurement.id == measurement_id)
        )
        return result.scalar_one_or_none()

    async def list_paginated(self, offset: int, limit: int) -> tuple[list[Measurement], int]:
        total_result = await self._session.execute(
            select(func.count()).select_from(Measurement)
        )
        total = total_result.scalar_one()

        result = await self._session.execute(
            select(Measurement)
            .order_by(Measurement.recorded_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_for_client(
        self, client_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[Measurement], int]:
        total_result = await self._session.execute(
            select(func.count())
            .select_from(Measurement)
            .where(Measurement.client_id == client_id)
        )
        total = total_result.scalar_one()

        result = await self._session.execute(
            select(Measurement)
            .where(Measurement.client_id == client_id)
            .order_by(Measurement.recorded_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_for_clients(
        self, client_ids: list[uuid.UUID], offset: int, limit: int
    ) -> tuple[list[Measurement], int]:
        if not client_ids:
            return [], 0

        total_result = await self._session.execute(
            select(func.count())
            .select_from(Measurement)
            .where(Measurement.client_id.in_(client_ids))
        )
        total = total_result.scalar_one()

        result = await self._session.execute(
            select(Measurement)
            .where(Measurement.client_id.in_(client_ids))
            .order_by(Measurement.recorded_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_all_for_client(self, client_id: uuid.UUID) -> list[Measurement]:
        result = await self._session.execute(
            select(Measurement)
            .where(Measurement.client_id == client_id)
            .order_by(Measurement.recorded_at.desc())
        )
        return list(result.scalars().all())
