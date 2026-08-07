import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.client import Client
from models.physical_assessment import PhysicalAssessment


@dataclass(frozen=True)
class LatestPhysicalAssessmentRow:
    """A client's most recent PhysicalAssessment, joined with the client's name."""

    client_id: uuid.UUID
    client_name: str
    recorded_at: datetime


class PhysicalAssessmentRepository(ABC):
    """Abstraction over physical assessment persistence, decoupling callers from SQLAlchemy.

    Physical assessments are editable during the configured edit window (see
    ApplicationSetting physical_assessment_edit_window_days), so update() is
    supported. There is intentionally no delete(): historical records are
    always preserved once recorded.
    """

    @abstractmethod
    async def create(self, physical_assessment: PhysicalAssessment) -> PhysicalAssessment: ...

    @abstractmethod
    async def update(self, physical_assessment: PhysicalAssessment) -> PhysicalAssessment: ...

    @abstractmethod
    async def get_by_id(self, physical_assessment_id: uuid.UUID) -> PhysicalAssessment | None: ...

    @abstractmethod
    async def list_paginated(self, offset: int, limit: int) -> tuple[list[PhysicalAssessment], int]: ...

    @abstractmethod
    async def list_for_client(
        self, client_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[PhysicalAssessment], int]: ...

    @abstractmethod
    async def list_for_clients(
        self, client_ids: list[uuid.UUID], offset: int, limit: int
    ) -> tuple[list[PhysicalAssessment], int]: ...

    @abstractmethod
    async def list_all_for_client(self, client_id: uuid.UUID) -> list[PhysicalAssessment]: ...

    @abstractmethod
    async def count_in_range(self, start: datetime, end: datetime) -> int: ...

    @abstractmethod
    async def get_latest_recorded_at_for_clients(
        self, client_ids: list[uuid.UUID] | None = None
    ) -> dict[uuid.UUID, datetime]: ...

    @abstractmethod
    async def list_latest_for_clients(
        self, client_ids: list[uuid.UUID] | None
    ) -> list[LatestPhysicalAssessmentRow]: ...


class SQLAlchemyPhysicalAssessmentRepository(PhysicalAssessmentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, physical_assessment: PhysicalAssessment) -> PhysicalAssessment:
        self._session.add(physical_assessment)
        await self._session.commit()
        await self._session.refresh(physical_assessment)
        return physical_assessment

    async def update(self, physical_assessment: PhysicalAssessment) -> PhysicalAssessment:
        await self._session.commit()
        await self._session.refresh(physical_assessment)
        return physical_assessment

    async def get_by_id(self, physical_assessment_id: uuid.UUID) -> PhysicalAssessment | None:
        result = await self._session.execute(
            select(PhysicalAssessment).where(PhysicalAssessment.id == physical_assessment_id)
        )
        return result.scalar_one_or_none()

    async def list_paginated(self, offset: int, limit: int) -> tuple[list[PhysicalAssessment], int]:
        total_result = await self._session.execute(
            select(func.count()).select_from(PhysicalAssessment)
        )
        total = total_result.scalar_one()

        result = await self._session.execute(
            select(PhysicalAssessment)
            .order_by(PhysicalAssessment.recorded_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_for_client(
        self, client_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[PhysicalAssessment], int]:
        total_result = await self._session.execute(
            select(func.count())
            .select_from(PhysicalAssessment)
            .where(PhysicalAssessment.client_id == client_id)
        )
        total = total_result.scalar_one()

        result = await self._session.execute(
            select(PhysicalAssessment)
            .where(PhysicalAssessment.client_id == client_id)
            .order_by(PhysicalAssessment.recorded_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_for_clients(
        self, client_ids: list[uuid.UUID], offset: int, limit: int
    ) -> tuple[list[PhysicalAssessment], int]:
        if not client_ids:
            return [], 0

        total_result = await self._session.execute(
            select(func.count())
            .select_from(PhysicalAssessment)
            .where(PhysicalAssessment.client_id.in_(client_ids))
        )
        total = total_result.scalar_one()

        result = await self._session.execute(
            select(PhysicalAssessment)
            .where(PhysicalAssessment.client_id.in_(client_ids))
            .order_by(PhysicalAssessment.recorded_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_all_for_client(self, client_id: uuid.UUID) -> list[PhysicalAssessment]:
        result = await self._session.execute(
            select(PhysicalAssessment)
            .where(PhysicalAssessment.client_id == client_id)
            .order_by(PhysicalAssessment.recorded_at.desc())
        )
        return list(result.scalars().all())

    async def count_in_range(self, start: datetime, end: datetime) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(PhysicalAssessment)
            .where(PhysicalAssessment.recorded_at >= start, PhysicalAssessment.recorded_at < end)
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
                partition_by=PhysicalAssessment.client_id,
                order_by=PhysicalAssessment.recorded_at.desc(),
            )
            .label("rn")
        )
        query = select(PhysicalAssessment.client_id, PhysicalAssessment.recorded_at, row_number)
        if client_ids is not None:
            query = query.where(PhysicalAssessment.client_id.in_(client_ids))
        ranked = query.subquery()

        result = await self._session.execute(
            select(ranked.c.client_id, ranked.c.recorded_at).where(ranked.c.rn == 1)
        )
        return {row.client_id: row.recorded_at for row in result}

    async def list_latest_for_clients(
        self, client_ids: list[uuid.UUID] | None
    ) -> list[LatestPhysicalAssessmentRow]:
        if client_ids is not None and not client_ids:
            return []

        row_number = (
            func.row_number()
            .over(
                partition_by=PhysicalAssessment.client_id,
                order_by=PhysicalAssessment.recorded_at.desc(),
            )
            .label("rn")
        )
        query = select(PhysicalAssessment.client_id, PhysicalAssessment.recorded_at, row_number)
        if client_ids is not None:
            query = query.where(PhysicalAssessment.client_id.in_(client_ids))
        ranked = query.subquery()

        result = await self._session.execute(
            select(ranked.c.client_id, Client.first_name, Client.last_name, ranked.c.recorded_at)
            .join(Client, Client.id == ranked.c.client_id)
            .where(ranked.c.rn == 1)
            .order_by(ranked.c.recorded_at.asc())
        )
        return [
            LatestPhysicalAssessmentRow(
                client_id=client_id,
                client_name=f"{first_name} {last_name}",
                recorded_at=recorded_at,
            )
            for client_id, first_name, last_name, recorded_at in result.all()
        ]
