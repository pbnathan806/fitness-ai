from abc import ABC, abstractmethod

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.application_setting import ApplicationSetting


class ApplicationSettingRepository(ABC):
    """Abstraction over application setting persistence, decoupling callers from SQLAlchemy."""

    @abstractmethod
    async def list_all(self) -> list[ApplicationSetting]: ...

    @abstractmethod
    async def get_by_key(self, key: str) -> ApplicationSetting | None: ...

    @abstractmethod
    async def update_value(self, key: str, value: str) -> ApplicationSetting | None: ...


class SQLAlchemyApplicationSettingRepository(ApplicationSettingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[ApplicationSetting]:
        result = await self._session.execute(
            select(ApplicationSetting).order_by(ApplicationSetting.key)
        )
        return list(result.scalars().all())

    async def get_by_key(self, key: str) -> ApplicationSetting | None:
        result = await self._session.execute(
            select(ApplicationSetting).where(ApplicationSetting.key == key)
        )
        return result.scalar_one_or_none()

    async def update_value(self, key: str, value: str) -> ApplicationSetting | None:
        await self._session.execute(
            update(ApplicationSetting)
            .where(ApplicationSetting.key == key)
            .values(value=value)
        )
        await self._session.commit()
        return await self.get_by_key(key)
