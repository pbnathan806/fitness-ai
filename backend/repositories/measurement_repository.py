import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.client import Client
from models.measurement import Measurement


@dataclass(frozen=True)
class LatestMeasurementRow:
    """A client's most recent Measurement, joined with the client's name."""

    client_id: uuid.UUID
    client_name: str
    recorded_at: datetime


class MeasurementRepository(ABC):
    """Abstraction over measurement persistence, decoupling callers from SQLAlchemy.

    Measurements are editable during the configured edit window (see
    ApplicationSetting measurement_edit_window_days), so update() is
    supported. There is intentionally no delete(): historical records are
    always preserved once recorded.
    """

    @abstractmethod
    async def create(self, measurement: Measurement) -> Measurement: ...

    @abstractmethod
    async def update(self, measurement: Measurement) -> Measurement: ...

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

    @abstractmethod
    async def count_in_range(self, start: datetime, end: datetime) -> int: ...

    @abstractmethod
    async def get_latest_recorded_at_for_clients(
        self, client_ids: list[uuid.UUID] | None = None
    ) -> dict[uuid.UUID, datetime]: ...

    @abstractmethod
    async def list_latest_for_clients(
        self, client_ids: list[uuid.UUID] | None
    ) -> list[LatestMeasurementRow]: ...


class SQLAlchemyMeasurementRepository(MeasurementRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, measurement: Measurement) -> Measurement:
        self._session.add(measurement)
        await self._session.commit()
        await self._session.refresh(measurement)
        return measurement

    async def update(self, measurement: Measurement) -> Measurement:
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

    async def count_in_range(self, start: datetime, end: datetime) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(Measurement)
            .where(Measurement.recorded_at >= start, Measurement.recorded_at < end)
        )
        return result.scalar_one()

    async def get_latest_recorded_at_for_clients(
        self, client_ids: list[uuid.UUID] | None = None
    ) -> dict[uuid.UUID, datetime]:
        if client_ids is not None and not client_ids:
            return {}

        row_number = (
            func.row_number()
            .over(
                partition_by=Measurement.client_id,
                order_by=Measurement.recorded_at.desc(),
            )
            .label("rn")
        )
        query = select(Measurement.client_id, Measurement.recorded_at, row_number)
        if client_ids is not None:
            query = query.where(Measurement.client_id.in_(client_ids))
        ranked = query.subquery()

        result = await self._session.execute(
            select(ranked.c.client_id, ranked.c.recorded_at).where(ranked.c.rn == 1)
        )
        return {row.client_id: row.recorded_at for row in result}

    async def list_latest_for_clients(
        self, client_ids: list[uuid.UUID] | None
    ) -> list[LatestMeasurementRow]:
        if client_ids is not None and not client_ids:
            return []

        row_number = (
            func.row_number()
            .over(
                partition_by=Measurement.client_id,
                order_by=Measurement.recorded_at.desc(),
            )
            .label("rn")
        )
        query = select(Measurement.client_id, Measurement.recorded_at, row_number)
        if client_ids is not None:
            query = query.where(Measurement.client_id.in_(client_ids))
        ranked = query.subquery()

        result = await self._session.execute(
            select(ranked.c.client_id, Client.first_name, Client.last_name, ranked.c.recorded_at)
            .join(Client, Client.id == ranked.c.client_id)
            .where(ranked.c.rn == 1)
            .order_by(ranked.c.recorded_at.asc())
        )
        return [
            LatestMeasurementRow(
                client_id=client_id,
                client_name=f"{first_name} {last_name}",
                recorded_at=recorded_at,
            )
            for client_id, first_name, last_name, recorded_at in result.all()
        ]
