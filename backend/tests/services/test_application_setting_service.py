import asyncio
import uuid
from datetime import datetime, timezone

import pytest

from core.constants import RoleName
from models.application_setting import ApplicationSetting
from repositories.application_setting_repository import ApplicationSettingRepository
from services.application_setting_service import (
    ApplicationSettingNotFoundError,
    ApplicationSettingService,
    ForbiddenError,
    InvalidSettingValueError,
)


class FakeApplicationSettingRepository(ApplicationSettingRepository):
    def __init__(self) -> None:
        self._settings: dict[str, ApplicationSetting] = {}

    def seed(self, setting: ApplicationSetting) -> None:
        self._settings[setting.key] = setting

    async def list_all(self) -> list[ApplicationSetting]:
        return sorted(self._settings.values(), key=lambda setting: setting.key)

    async def get_by_key(self, key: str) -> ApplicationSetting | None:
        return self._settings.get(key)

    async def update_value(self, key: str, value: str) -> ApplicationSetting | None:
        setting = self._settings.get(key)
        if setting is None:
            return None
        setting.value = value
        setting.updated_at = datetime.now(timezone.utc)
        return setting


def _make_setting(**overrides) -> ApplicationSetting:
    defaults = dict(
        id=uuid.uuid4(),
        key="measurement_overdue_days",
        value="14",
        description="Days after which measurements are overdue.",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return ApplicationSetting(**defaults)


def _make_service() -> tuple[ApplicationSettingService, FakeApplicationSettingRepository]:
    repository = FakeApplicationSettingRepository()
    service = ApplicationSettingService(repository)
    return service, repository


def test_list_settings_returns_all():
    service, repository = _make_service()
    repository.seed(_make_setting(key="measurement_overdue_days", value="14"))
    repository.seed(_make_setting(key="subscription_expired_days", value="30"))

    settings = asyncio.run(service.list_settings())

    assert {setting.key for setting in settings} == {
        "measurement_overdue_days",
        "subscription_expired_days",
    }


def test_get_setting_succeeds():
    service, repository = _make_service()
    repository.seed(_make_setting(key="measurement_overdue_days", value="14"))

    detail = asyncio.run(service.get_setting("measurement_overdue_days"))

    assert detail.value == "14"


def test_get_setting_raises_not_found():
    service, _ = _make_service()

    with pytest.raises(ApplicationSettingNotFoundError):
        asyncio.run(service.get_setting("does_not_exist"))


def test_update_setting_succeeds_for_super_admin():
    service, repository = _make_service()
    repository.seed(_make_setting(key="measurement_overdue_days", value="14"))

    detail = asyncio.run(
        service.update_setting(
            actor_role=RoleName.SUPER_ADMIN, key="measurement_overdue_days", value="21"
        )
    )

    assert detail.value == "21"


def test_update_setting_rejects_non_super_admin():
    service, repository = _make_service()
    repository.seed(_make_setting(key="measurement_overdue_days", value="14"))

    for role in (RoleName.TRAINER, RoleName.CLIENT, None):
        with pytest.raises(ForbiddenError):
            asyncio.run(
                service.update_setting(
                    actor_role=role, key="measurement_overdue_days", value="21"
                )
            )


def test_update_setting_raises_not_found():
    service, _ = _make_service()

    with pytest.raises(ApplicationSettingNotFoundError):
        asyncio.run(
            service.update_setting(
                actor_role=RoleName.SUPER_ADMIN, key="does_not_exist", value="21"
            )
        )


def test_get_int_parses_stored_value():
    service, repository = _make_service()
    repository.seed(_make_setting(key="measurement_overdue_days", value="14"))

    assert asyncio.run(service.get_int("measurement_overdue_days")) == 14


def test_get_int_raises_on_non_numeric_value():
    service, repository = _make_service()
    repository.seed(_make_setting(key="measurement_overdue_days", value="not-a-number"))

    with pytest.raises(InvalidSettingValueError):
        asyncio.run(service.get_int("measurement_overdue_days"))


def test_get_string_returns_raw_value():
    service, repository = _make_service()
    repository.seed(_make_setting(key="some_setting", value="hello"))

    assert asyncio.run(service.get_string("some_setting")) == "hello"


@pytest.mark.parametrize("stored_value, expected", [("true", True), ("1", True), ("false", False), ("0", False)])
def test_get_bool_parses_stored_value(stored_value, expected):
    service, repository = _make_service()
    repository.seed(_make_setting(key="some_flag", value=stored_value))

    assert asyncio.run(service.get_bool("some_flag")) is expected


def test_get_bool_raises_on_invalid_value():
    service, repository = _make_service()
    repository.seed(_make_setting(key="some_flag", value="maybe"))

    with pytest.raises(InvalidSettingValueError):
        asyncio.run(service.get_bool("some_flag"))
