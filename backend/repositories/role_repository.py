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
