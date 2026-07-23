import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.session import Session, SessionStatus

_ACTIVE_SESSION_STATUSES = (
    SessionStatus.SCHEDULED,
    SessionStatus.COMPLETED,
    SessionStatus.RESCHEDULED,
)


class SessionRepository(ABC):
    """Abstraction over session persistence, decoupling callers from SQLAlchemy."""

    @abstractmethod
    async def create(self, session: Session) -> Session: ...

    @abstractmethod
    async def get_by_id(self, session_id: uuid.UUID) -> Session | None: ...

    @abstractmethod
    async def update(self, session_id: uuid.UUID, values: dict) -> Session | None: ...

    @abstractmethod
    async def list_paginated(self, offset: int, limit: int) -> tuple[list[Session], int]: ...

    @abstractmethod
    async def list_for_trainer(
        self, trainer_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[Session], int]: ...

    @abstractmethod
    async def list_for_client(
        self, client_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[Session], int]: ...

    @abstractmethod
    async def list_all_for_client(self, client_id: uuid.UUID) -> list[Session]: ...

    @abstractmethod
    async def trainer_has_overlap(
        self, trainer_id: uuid.UUID, start: datetime, end: datetime
    ) -> bool: ...

    @abstractmethod
    async def client_has_overlap(
        self, client_id: uuid.UUID, start: datetime, end: datetime
    ) -> bool: ...

    @abstractmethod
    async def count_active_for_client(self, client_id: uuid.UUID) -> int: ...

    @abstractmethod
    async def count_in_range(
        self,
        start: datetime,
        end: datetime,
        *,
        trainer_id: uuid.UUID | None = None,
        client_id: uuid.UUID | None = None,
        exclude_cancelled: bool = False,
    ) -> int: ...


class SQLAlchemySessionRepository(SessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, session: Session) -> Session:
        self._session.add(session)
        await self._session.commit()
        await self._session.refresh(session)
        return session

    async def get_by_id(self, session_id: uuid.UUID) -> Session | None:
        result = await self._session.execute(select(Session).where(Session.id == session_id))
        return result.scalar_one_or_none()

    async def update(self, session_id: uuid.UUID, values: dict) -> Session | None:
        if values:
            await self._session.execute(
                update(Session).where(Session.id == session_id).values(**values)
            )
            await self._session.commit()
        return await self.get_by_id(session_id)

    async def list_paginated(self, offset: int, limit: int) -> tuple[list[Session], int]:
        total_result = await self._session.execute(select(func.count()).select_from(Session))
        total = total_result.scalar_one()

        result = await self._session.execute(
            select(Session).order_by(Session.scheduled_start.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_for_trainer(
        self, trainer_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[Session], int]:
        total_result = await self._session.execute(
            select(func.count()).select_from(Session).where(Session.trainer_id == trainer_id)
        )
        total = total_result.scalar_one()

        result = await self._session.execute(
            select(Session)
            .where(Session.trainer_id == trainer_id)
            .order_by(Session.scheduled_start.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_for_client(
        self, client_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[Session], int]:
        total_result = await self._session.execute(
            select(func.count()).select_from(Session).where(Session.client_id == client_id)
        )
        total = total_result.scalar_one()

        result = await self._session.execute(
            select(Session)
            .where(Session.client_id == client_id)
            .order_by(Session.scheduled_start.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_all_for_client(self, client_id: uuid.UUID) -> list[Session]:
        result = await self._session.execute(
            select(Session)
            .where(Session.client_id == client_id)
            .order_by(Session.scheduled_start.desc())
        )
        return list(result.scalars().all())

    async def trainer_has_overlap(
        self, trainer_id: uuid.UUID, start: datetime, end: datetime
    ) -> bool:
        result = await self._session.execute(
            select(Session.id).where(
                Session.trainer_id == trainer_id,
                Session.status != SessionStatus.CANCELLED,
                Session.scheduled_start < end,
                Session.scheduled_end > start,
            )
        )
        return result.first() is not None

    async def client_has_overlap(
        self, client_id: uuid.UUID, start: datetime, end: datetime
    ) -> bool:
        result = await self._session.execute(
            select(Session.id).where(
                Session.client_id == client_id,
                Session.status != SessionStatus.CANCELLED,
                Session.scheduled_start < end,
                Session.scheduled_end > start,
            )
        )
        return result.first() is not None

    async def count_active_for_client(self, client_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(Session)
            .where(
                Session.client_id == client_id,
                Session.status.in_(_ACTIVE_SESSION_STATUSES),
            )
        )
        return result.scalar_one()

    async def count_in_range(
        self,
        start: datetime,
        end: datetime,
        *,
        trainer_id: uuid.UUID | None = None,
        client_id: uuid.UUID | None = None,
        exclude_cancelled: bool = False,
    ) -> int:
        conditions = [Session.scheduled_start >= start, Session.scheduled_start < end]
        if trainer_id is not None:
            conditions.append(Session.trainer_id == trainer_id)
        if client_id is not None:
            conditions.append(Session.client_id == client_id)
        if exclude_cancelled:
            conditions.append(Session.status != SessionStatus.CANCELLED)

        result = await self._session.execute(
            select(func.count()).select_from(Session).where(*conditions)
        )
        return result.scalar_one()
