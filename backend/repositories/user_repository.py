import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.user import User


class UserRepository(ABC):
    """Abstraction over user persistence, decoupling callers from SQLAlchemy."""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def update_last_login(self, user_id: uuid.UUID, login_time: datetime) -> None: ...

    @abstractmethod
    async def update_password_hash(self, user_id: uuid.UUID, password_hash: str) -> None: ...

    @abstractmethod
    async def create(self, email: str, password_hash: str) -> User: ...


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def update_last_login(self, user_id: uuid.UUID, login_time: datetime) -> None:
        await self._session.execute(
            update(User).where(User.id == user_id).values(last_login_at=login_time)
        )
        await self._session.commit()

    async def update_password_hash(self, user_id: uuid.UUID, password_hash: str) -> None:
        await self._session.execute(
            update(User).where(User.id == user_id).values(password_hash=password_hash)
        )
        await self._session.commit()

    async def create(self, email: str, password_hash: str) -> User:
        user = User(email=email, password_hash=password_hash)
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user
