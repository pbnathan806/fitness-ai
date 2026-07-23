from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import RoleName
from core.deps import CurrentUser, get_current_user
from database.session import get_db
from repositories.application_setting_repository import (
    ApplicationSettingRepository,
    SQLAlchemyApplicationSettingRepository,
)
from schemas.application_setting import (
    ApplicationSettingResponse,
    ApplicationSettingUpdateRequest,
)
from services.application_setting_service import (
    ApplicationSettingDetail,
    ApplicationSettingNotFoundError,
    ApplicationSettingService,
    ForbiddenError,
)

router = APIRouter(prefix="/api/v1/application-settings", tags=["application-settings"])


def get_application_setting_repository(
    session: AsyncSession = Depends(get_db),
) -> ApplicationSettingRepository:
    return SQLAlchemyApplicationSettingRepository(session)


def get_application_setting_service(
    application_setting_repository: ApplicationSettingRepository = Depends(
        get_application_setting_repository
    ),
) -> ApplicationSettingService:
    return ApplicationSettingService(application_setting_repository)


def _to_response(detail: ApplicationSettingDetail) -> ApplicationSettingResponse:
    return ApplicationSettingResponse(
        id=detail.id,
        key=detail.key,
        value=detail.value,
        description=detail.description,
        created_at=detail.created_at,
        updated_at=detail.updated_at,
    )


def _require_super_admin(current_user: CurrentUser) -> None:
    if current_user.active_role != RoleName.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admins may access application settings.",
        )


@router.get("", response_model=list[ApplicationSettingResponse], status_code=status.HTTP_200_OK)
async def list_application_settings(
    current_user: CurrentUser = Depends(get_current_user),
    application_setting_service: ApplicationSettingService = Depends(
        get_application_setting_service
    ),
) -> list[ApplicationSettingResponse]:
    _require_super_admin(current_user)
    items = await application_setting_service.list_settings()
    return [_to_response(item) for item in items]


@router.get(
    "/{key}", response_model=ApplicationSettingResponse, status_code=status.HTTP_200_OK
)
async def get_application_setting(
    key: str,
    current_user: CurrentUser = Depends(get_current_user),
    application_setting_service: ApplicationSettingService = Depends(
        get_application_setting_service
    ),
) -> ApplicationSettingResponse:
    _require_super_admin(current_user)
    try:
        detail = await application_setting_service.get_setting(key)
    except ApplicationSettingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)


@router.patch(
    "/{key}", response_model=ApplicationSettingResponse, status_code=status.HTTP_200_OK
)
async def update_application_setting(
    key: str,
    payload: ApplicationSettingUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    application_setting_service: ApplicationSettingService = Depends(
        get_application_setting_service
    ),
) -> ApplicationSettingResponse:
    try:
        detail = await application_setting_service.update_setting(
            actor_role=current_user.active_role,
            key=key,
            value=payload.value,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ApplicationSettingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)
