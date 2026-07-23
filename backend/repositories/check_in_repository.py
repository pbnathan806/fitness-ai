import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.check_in import CheckIn


class CheckInRepository(ABC):
    """Abstraction over check-in persistence, decoupling callers from SQLAlchemy.

    Deliberately has no update()/delete() method: check-ins are immutable
    and historical records are always preserved.
    """

    @abstractmethod
    async def create(self, check_in: CheckIn) -> CheckIn: ...

    @abstractmethod
    async def get_by_id(self, check_in_id: uuid.UUID) -> CheckIn | None: ...

    @abstractmethod
    async def get_for_client_in_range(
        self, client_id: uuid.UUID, start: datetime, end: datetime
    ) -> CheckIn | None: ...

    @abstractmethod
    async def list_paginated(self, offset: int, limit: int) -> tuple[list[CheckIn], int]: ...

    @abstractmethod
    async def list_for_client(
        self, client_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[CheckIn], int]: ...

    @abstractmethod
    async def list_for_clients(
        self, client_ids: list[uuid.UUID], offset: int, limit: int
    ) -> tuple[list[CheckIn], int]: ...

    @abstractmethod
    async def list_all_for_client(self, client_id: uuid.UUID) -> list[CheckIn]: ...


class SQLAlchemyCheckInRepository(CheckInRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, check_in: CheckIn) -> CheckIn:
        self._session.add(check_in)
        await self._session.commit()
        await self._session.refresh(check_in)
        return check_in

    async def get_by_id(self, check_in_id: uuid.UUID) -> CheckIn | None:
        result = await self._session.execute(
            select(CheckIn).where(CheckIn.id == check_in_id)
        )
        return result.scalar_one_or_none()

    async def get_for_client_in_range(
        self, client_id: uuid.UUID, start: datetime, end: datetime
    ) -> CheckIn | None:
        result = await self._session.execute(
            select(CheckIn).where(
                CheckIn.client_id == client_id,
                CheckIn.submitted_at >= start,
                CheckIn.submitted_at < end,
            )
        )
        return result.scalar_one_or_none()

    async def list_paginated(self, offset: int, limit: int) -> tuple[list[CheckIn], int]:
        total_result = await self._session.execute(
            select(func.count()).select_from(CheckIn)
        )
        total = total_result.scalar_one()

        result = await self._session.execute(
            select(CheckIn)
            .order_by(CheckIn.submitted_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_for_client(
        self, client_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[CheckIn], int]:
        total_result = await self._session.execute(
            select(func.count()).select_from(CheckIn).where(CheckIn.client_id == client_id)
        )
        total = total_result.scalar_one()

        result = await self._session.execute(
            select(CheckIn)
            .where(CheckIn.client_id == client_id)
            .order_by(CheckIn.submitted_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_for_clients(
        self, client_ids: list[uuid.UUID], offset: int, limit: int
    ) -> tuple[list[CheckIn], int]:
        if not client_ids:
            return [], 0

        total_result = await self._session.execute(
            select(func.count())
            .select_from(CheckIn)
            .where(CheckIn.client_id.in_(client_ids))
        )
        total = total_result.scalar_one()

        result = await self._session.execute(
            select(CheckIn)
            .where(CheckIn.client_id.in_(client_ids))
            .order_by(CheckIn.submitted_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_all_for_client(self, client_id: uuid.UUID) -> list[CheckIn]:
        result = await self._session.execute(
            select(CheckIn)
            .where(CheckIn.client_id == client_id)
            .order_by(CheckIn.submitted_at.desc())
        )
        return list(result.scalars().all())
