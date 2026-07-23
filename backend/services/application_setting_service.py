import uuid
from dataclasses import dataclass
from datetime import datetime

from core.constants import RoleName
from repositories.application_setting_repository import ApplicationSettingRepository

_TRUE_VALUES = {"true", "1"}
_FALSE_VALUES = {"false", "0"}


class ForbiddenError(Exception):
    """Raised when the acting user's role does not permit the requested action."""


class ApplicationSettingNotFoundError(Exception):
    """Raised when no application setting exists for the requested key."""


class InvalidSettingValueError(Exception):
    """Raised when a setting's stored value cannot be parsed as the requested type."""


@dataclass(frozen=True)
class ApplicationSettingDetail:
    id: uuid.UUID
    key: str
    value: str
    description: str | None
    created_at: datetime
    updated_at: datetime


def _to_detail(setting) -> ApplicationSettingDetail:
    return ApplicationSettingDetail(
        id=setting.id,
        key=setting.key,
        value=setting.value,
        description=setting.description,
        created_at=setting.created_at,
        updated_at=setting.updated_at,
    )


class ApplicationSettingService:
    """Business logic for DB-backed operational settings (Task-20).

    Consuming services (e.g. the future Dashboard module) should read
    operational thresholds through get_int/get_string/get_bool instead of
    hardcoding them, so values can be changed at runtime by a SUPER_ADMIN
    without a deployment.
    """

    def __init__(self, application_setting_repository: ApplicationSettingRepository) -> None:
        self._application_setting_repository = application_setting_repository

    async def list_settings(self) -> list[ApplicationSettingDetail]:
        settings = await self._application_setting_repository.list_all()
        return [_to_detail(setting) for setting in settings]

    async def get_setting(self, key: str) -> ApplicationSettingDetail:
        setting = await self._application_setting_repository.get_by_key(key)
        if setting is None:
            raise ApplicationSettingNotFoundError(f"Application setting '{key}' was not found.")
        return _to_detail(setting)

    async def update_setting(
        self, actor_role: str | None, key: str, value: str
    ) -> ApplicationSettingDetail:
        if actor_role != RoleName.SUPER_ADMIN:
            raise ForbiddenError("Only Super Admins may update application settings.")

        if await self._application_setting_repository.get_by_key(key) is None:
            raise ApplicationSettingNotFoundError(f"Application setting '{key}' was not found.")

        setting = await self._application_setting_repository.update_value(key, value)
        return _to_detail(setting)

    async def get_string(self, key: str) -> str:
        detail = await self.get_setting(key)
        return detail.value

    async def get_int(self, key: str) -> int:
        detail = await self.get_setting(key)
        try:
            return int(detail.value)
        except ValueError as exc:
            raise InvalidSettingValueError(
                f"Application setting '{key}' value '{detail.value}' is not a valid integer."
            ) from exc

    async def get_bool(self, key: str) -> bool:
        detail = await self.get_setting(key)
        normalized = detail.value.strip().lower()
        if normalized in _TRUE_VALUES:
            return True
        if normalized in _FALSE_VALUES:
            return False
        raise InvalidSettingValueError(
            f"Application setting '{key}' value '{detail.value}' is not a valid boolean."
        )
