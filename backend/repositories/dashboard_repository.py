import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.check_in import CheckIn
from models.session import Session, SessionStatus
from models.trainer_profile import TrainerProfile


class DashboardRepository(ABC):
    """Aggregate queries for Task-21 dashboards that don't belong to any single
    existing table-scoped repository (either because no repository owns that
    table yet, e.g. trainer_profiles, or because the query joins across
    tables owned by different repositories).
    """

    @abstractmethod
    async def count_total_trainers(self) -> int: ...

    @abstractmethod
    async def count_pending_check_ins(
        self,
        client_ids: list[uuid.UUID] | None,
        day_start: datetime,
        day_end: datetime,
        now: datetime,
    ) -> int: ...


class SQLAlchemyDashboardRepository(DashboardRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count_total_trainers(self) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(TrainerProfile)
        )
        return result.scalar_one()

    async def count_pending_check_ins(
        self,
        client_ids: list[uuid.UUID] | None,
        day_start: datetime,
        day_end: datetime,
        now: datetime,
    ) -> int:
        if client_ids is not None and not client_ids:
            return 0

        has_check_in_today = exists(
            select(CheckIn.id).where(
                CheckIn.client_id == Session.client_id,
                CheckIn.submitted_at >= day_start,
                CheckIn.submitted_at < day_end,
            )
        )

        conditions = [
            Session.status != SessionStatus.CANCELLED,
            Session.scheduled_start >= day_start,
            Session.scheduled_start < day_end,
            Session.scheduled_start < now,
            ~has_check_in_today,
        ]
        if client_ids is not None:
            conditions.append(Session.client_id.in_(client_ids))

        result = await self._session.execute(
            select(func.count()).select_from(Session).where(*conditions)
        )
        return result.scalar_one()
