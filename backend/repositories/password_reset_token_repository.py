import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.password_reset_token import PasswordResetToken


class PasswordResetTokenRepository(ABC):
    """Abstraction over password reset token persistence, decoupling callers from SQLAlchemy."""

    @abstractmethod
    async def create(
        self, user_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> PasswordResetToken: ...

    @abstractmethod
    async def get_valid_by_token_hash(
        self, token_hash: str, now: datetime
    ) -> PasswordResetToken | None: ...

    @abstractmethod
    async def mark_used(self, token_id: uuid.UUID, used_at: datetime) -> None: ...

    @abstractmethod
    async def invalidate_active_tokens_for_user(
        self, user_id: uuid.UUID, used_at: datetime
    ) -> None: ...


class SQLAlchemyPasswordResetTokenRepository(PasswordResetTokenRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, user_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> PasswordResetToken:
        token = PasswordResetToken(
            user_id=user_id, token_hash=token_hash, expires_at=expires_at
        )
        self._session.add(token)
        await self._session.commit()
        await self._session.refresh(token)
        return token

    async def get_valid_by_token_hash(
        self, token_hash: str, now: datetime
    ) -> PasswordResetToken | None:
        result = await self._session.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    async def mark_used(self, token_id: uuid.UUID, used_at: datetime) -> None:
        await self._session.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.id == token_id)
            .values(used_at=used_at)
        )
        await self._session.commit()

    async def invalidate_active_tokens_for_user(
        self, user_id: uuid.UUID, used_at: datetime
    ) -> None:
        await self._session.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=used_at)
        )
        await self._session.commit()
