import uuid
from abc import ABC, abstractmethod

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.subscription_plan import SubscriptionPlan


class SubscriptionPlanRepository(ABC):
    """Abstraction over subscription plan catalog persistence, decoupling callers from SQLAlchemy."""

    @abstractmethod
    async def create(self, plan: SubscriptionPlan) -> SubscriptionPlan: ...

    @abstractmethod
    async def get_by_id(self, plan_id: uuid.UUID) -> SubscriptionPlan | None: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> SubscriptionPlan | None: ...

    @abstractmethod
    async def list_active(self) -> list[SubscriptionPlan]: ...

    @abstractmethod
    async def update(self, plan_id: uuid.UUID, values: dict) -> SubscriptionPlan | None: ...


class SQLAlchemySubscriptionPlanRepository(SubscriptionPlanRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, plan: SubscriptionPlan) -> SubscriptionPlan:
        self._session.add(plan)
        await self._session.commit()
        await self._session.refresh(plan)
        return plan

    async def get_by_id(self, plan_id: uuid.UUID) -> SubscriptionPlan | None:
        result = await self._session.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> SubscriptionPlan | None:
        result = await self._session.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.name == name)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[SubscriptionPlan]:
        result = await self._session.execute(
            select(SubscriptionPlan)
            .where(SubscriptionPlan.is_active.is_(True))
            .order_by(SubscriptionPlan.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(self, plan_id: uuid.UUID, values: dict) -> SubscriptionPlan | None:
        if values:
            await self._session.execute(
                update(SubscriptionPlan).where(SubscriptionPlan.id == plan_id).values(**values)
            )
            await self._session.commit()
        return await self.get_by_id(plan_id)
