import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import exists, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.check_in import CheckIn
from models.client import Client
from models.session import Session, SessionStatus


@dataclass(frozen=True)
class PendingCheckInRow:
    """A non-cancelled, already-started Session with no Check-in yet."""

    session_id: uuid.UUID
    client_id: uuid.UUID
    client_name: str
    scheduled_start: datetime


class CheckInRepository(ABC):
    """Abstraction over check-in persistence, decoupling callers from SQLAlchemy.

    Check-ins are editable during the configured edit window (see
    ApplicationSetting check_in_edit_window_days), so update() is supported.
    There is intentionally no delete(): historical records are always
    preserved once submitted.
    """

    @abstractmethod
    async def create(self, check_in: CheckIn) -> CheckIn: ...

    @abstractmethod
    async def update(self, check_in: CheckIn) -> CheckIn: ...

    @abstractmethod
    async def get_by_id(self, check_in_id: uuid.UUID) -> CheckIn | None: ...

    @abstractmethod
    async def get_by_session_id(self, session_id: uuid.UUID) -> CheckIn | None: ...

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

    @abstractmethod
    async def count_in_range(
        self, start: datetime, end: datetime, client_ids: list[uuid.UUID] | None = None
    ) -> int: ...

    @abstractmethod
    async def list_pending(
        self, client_ids: list[uuid.UUID] | None, now: datetime
    ) -> list[PendingCheckInRow]: ...

    @abstractmethod
    async def count_pending(self, client_ids: list[uuid.UUID] | None, now: datetime) -> int: ...

    @abstractmethod
    async def count_for_client(self, client_id: uuid.UUID) -> int: ...


class SQLAlchemyCheckInRepository(CheckInRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, check_in: CheckIn) -> CheckIn:
        self._session.add(check_in)
        await self._session.commit()
        await self._session.refresh(check_in)
        return check_in

    async def update(self, check_in: CheckIn) -> CheckIn:
        await self._session.commit()
        await self._session.refresh(check_in)
        return check_in

    async def get_by_id(self, check_in_id: uuid.UUID) -> CheckIn | None:
        result = await self._session.execute(
            select(CheckIn).where(CheckIn.id == check_in_id)
        )
        return result.scalar_one_or_none()

    async def get_by_session_id(self, session_id: uuid.UUID) -> CheckIn | None:
        result = await self._session.execute(
            select(CheckIn).where(CheckIn.session_id == session_id)
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

    async def count_in_range(
        self, start: datetime, end: datetime, client_ids: list[uuid.UUID] | None = None
    ) -> int:
        conditions = [CheckIn.submitted_at >= start, CheckIn.submitted_at < end]
        if client_ids is not None:
            if not client_ids:
                return 0
            conditions.append(CheckIn.client_id.in_(client_ids))

        result = await self._session.execute(
            select(func.count()).select_from(CheckIn).where(*conditions)
        )
        return result.scalar_one()

    async def list_pending(
        self, client_ids: list[uuid.UUID] | None, now: datetime
    ) -> list[PendingCheckInRow]:
        if client_ids is not None and not client_ids:
            return []

        has_check_in = exists(
            select(CheckIn.id).where(CheckIn.session_id == Session.id)
        )
        conditions = [
            Session.status != SessionStatus.CANCELLED,
            Session.scheduled_start < now,
            ~has_check_in,
        ]
        if client_ids is not None:
            conditions.append(Session.client_id.in_(client_ids))

        result = await self._session.execute(
            select(
                Session.id, Session.client_id, Client.first_name, Client.last_name,
                Session.scheduled_start,
            )
            .join(Client, Client.id == Session.client_id)
            .where(*conditions)
            .order_by(Session.scheduled_start.asc())
        )
        return [
            PendingCheckInRow(
                session_id=session_id,
                client_id=client_id,
                client_name=f"{first_name} {last_name}",
                scheduled_start=scheduled_start,
            )
            for session_id, client_id, first_name, last_name, scheduled_start in result.all()
        ]

    async def count_pending(self, client_ids: list[uuid.UUID] | None, now: datetime) -> int:
        if client_ids is not None and not client_ids:
            return 0

        has_check_in = exists(
            select(CheckIn.id).where(CheckIn.session_id == Session.id)
        )
        conditions = [
            Session.status != SessionStatus.CANCELLED,
            Session.scheduled_start < now,
            ~has_check_in,
        ]
        if client_ids is not None:
            conditions.append(Session.client_id.in_(client_ids))

        result = await self._session.execute(
            select(func.count()).select_from(Session).where(*conditions)
        )
        return result.scalar_one()

    async def count_for_client(self, client_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(CheckIn).where(CheckIn.client_id == client_id)
        )
        return result.scalar_one()
