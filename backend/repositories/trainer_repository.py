import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.trainer_profile import TrainerProfile
from models.user import User

_SORTABLE_FIELDS = {
    "created_at": TrainerProfile.created_at,
    "first_name": TrainerProfile.first_name,
}


@dataclass(frozen=True)
class TrainerRecord:
    """A trainer profile joined with its account email.

    Email lives on `users`, not `trainer_profiles`, so reads join both tables
    rather than requiring callers to make a second round trip through
    UserRepository for every trainer returned (including list pages).
    """

    trainer: TrainerProfile
    email: str


class TrainerRepository(ABC):
    """Abstraction over trainer profile persistence, decoupling callers from SQLAlchemy."""

    @abstractmethod
    async def create(self, trainer: TrainerProfile) -> TrainerProfile: ...

    @abstractmethod
    async def get_by_id(self, trainer_id: uuid.UUID) -> TrainerRecord | None: ...

    @abstractmethod
    async def get_by_user_id(self, user_id: uuid.UUID) -> TrainerRecord | None: ...

    @abstractmethod
    async def update(self, trainer_id: uuid.UUID, values: dict) -> TrainerRecord | None: ...

    @abstractmethod
    async def list_paginated(
        self,
        offset: int,
        limit: int,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        is_active: bool | None = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> tuple[list[TrainerRecord], int]: ...


class SQLAlchemyTrainerRepository(TrainerRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, trainer: TrainerProfile) -> TrainerProfile:
        self._session.add(trainer)
        await self._session.commit()
        await self._session.refresh(trainer)
        return trainer

    async def get_by_id(self, trainer_id: uuid.UUID) -> TrainerRecord | None:
        result = await self._session.execute(
            select(TrainerProfile, User.email)
            .join(User, User.id == TrainerProfile.user_id)
            .where(TrainerProfile.id == trainer_id)
        )
        row = result.first()
        if row is None:
            return None
        trainer, email = row
        return TrainerRecord(trainer=trainer, email=email)

    async def get_by_user_id(self, user_id: uuid.UUID) -> TrainerRecord | None:
        result = await self._session.execute(
            select(TrainerProfile, User.email)
            .join(User, User.id == TrainerProfile.user_id)
            .where(TrainerProfile.user_id == user_id)
        )
        row = result.first()
        if row is None:
            return None
        trainer, email = row
        return TrainerRecord(trainer=trainer, email=email)

    async def update(self, trainer_id: uuid.UUID, values: dict) -> TrainerRecord | None:
        if values:
            await self._session.execute(
                update(TrainerProfile).where(TrainerProfile.id == trainer_id).values(**values)
            )
            await self._session.commit()
        return await self.get_by_id(trainer_id)

    async def list_paginated(
        self,
        offset: int,
        limit: int,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        is_active: bool | None = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> tuple[list[TrainerRecord], int]:
        conditions = []
        if first_name:
            conditions.append(TrainerProfile.first_name.ilike(f"%{first_name}%"))
        if last_name:
            conditions.append(TrainerProfile.last_name.ilike(f"%{last_name}%"))
        if email:
            conditions.append(User.email.ilike(f"%{email}%"))
        if is_active is not None:
            conditions.append(TrainerProfile.is_active.is_(is_active))

        base_query = select(TrainerProfile, User.email).join(User, User.id == TrainerProfile.user_id)
        if conditions:
            base_query = base_query.where(*conditions)

        total_result = await self._session.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = total_result.scalar_one()

        sort_column = _SORTABLE_FIELDS.get(sort_by, TrainerProfile.created_at)
        order = sort_column.desc() if sort_desc else sort_column.asc()

        result = await self._session.execute(
            base_query.order_by(order).offset(offset).limit(limit)
        )
        records = [TrainerRecord(trainer=trainer, email=email) for trainer, email in result.all()]
        return records, total
