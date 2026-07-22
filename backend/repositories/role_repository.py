import uuid
from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.role import Role
from models.user_role import UserRole


class RoleRepository(ABC):
    """Abstraction over role lookups, decoupling callers from SQLAlchemy."""

    @abstractmethod
    async def get_role_names_for_user(self, user_id: uuid.UUID) -> list[str]: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Role | None: ...

    @abstractmethod
    async def assign_role_to_user(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None: ...


class SQLAlchemyRoleRepository(RoleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_role_names_for_user(self, user_id: uuid.UUID) -> list[str]:
        result = await self._session.execute(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
            .order_by(Role.name)
        )
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Role | None:
        result = await self._session.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def assign_role_to_user(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        self._session.add(UserRole(user_id=user_id, role_id=role_id))
        await self._session.commit()
