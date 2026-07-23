import uuid
from abc import ABC, abstractmethod

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.subscription import Subscription, SubscriptionStatus


class SubscriptionRepository(ABC):
    """Abstraction over subscription persistence, decoupling callers from SQLAlchemy."""

    @abstractmethod
    async def create(self, subscription: Subscription) -> Subscription: ...

    @abstractmethod
    async def get_by_id(self, subscription_id: uuid.UUID) -> Subscription | None: ...

    @abstractmethod
    async def list_paginated(
        self, offset: int, limit: int
    ) -> tuple[list[Subscription], int]: ...

    @abstractmethod
    async def list_for_client(self, client_id: uuid.UUID) -> list[Subscription]: ...

    @abstractmethod
    async def get_active_for_client(self, client_id: uuid.UUID) -> Subscription | None: ...

    @abstractmethod
    async def get_latest_for_client(self, client_id: uuid.UUID) -> Subscription | None: ...

    @abstractmethod
    async def update(self, subscription_id: uuid.UUID, values: dict) -> Subscription | None: ...


class SQLAlchemySubscriptionRepository(SubscriptionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, subscription: Subscription) -> Subscription:
        self._session.add(subscription)
        await self._session.commit()
        await self._session.refresh(subscription)
        return subscription

    async def get_by_id(self, subscription_id: uuid.UUID) -> Subscription | None:
        result = await self._session.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        return result.scalar_one_or_none()

    async def list_paginated(
        self, offset: int, limit: int
    ) -> tuple[list[Subscription], int]:
        total_result = await self._session.execute(
            select(func.count()).select_from(Subscription)
        )
        total = total_result.scalar_one()

        result = await self._session.execute(
            select(Subscription)
            .order_by(Subscription.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_for_client(self, client_id: uuid.UUID) -> list[Subscription]:
        result = await self._session.execute(
            select(Subscription)
            .where(Subscription.client_id == client_id)
            .order_by(Subscription.start_date.desc())
        )
        return list(result.scalars().all())

    async def get_active_for_client(self, client_id: uuid.UUID) -> Subscription | None:
        result = await self._session.execute(
            select(Subscription).where(
                Subscription.client_id == client_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_for_client(self, client_id: uuid.UUID) -> Subscription | None:
        result = await self._session.execute(
            select(Subscription)
            .where(Subscription.client_id == client_id)
            .order_by(Subscription.start_date.desc(), Subscription.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update(self, subscription_id: uuid.UUID, values: dict) -> Subscription | None:
        if values:
            await self._session.execute(
                update(Subscription).where(Subscription.id == subscription_id).values(**values)
            )
            await self._session.commit()
        return await self.get_by_id(subscription_id)
