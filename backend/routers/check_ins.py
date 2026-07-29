import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import CurrentUser, get_current_user
from database.session import get_db
from repositories.application_setting_repository import (
    ApplicationSettingRepository,
    SQLAlchemyApplicationSettingRepository,
)
from repositories.assignment_repository import (
    AssignmentRepository,
    SQLAlchemyAssignmentRepository,
)
from repositories.check_in_repository import CheckInRepository, SQLAlchemyCheckInRepository
from repositories.client_repository import ClientRepository, SQLAlchemyClientRepository
from repositories.session_repository import SessionRepository, SQLAlchemySessionRepository
from schemas.check_in import (
    CheckInCreateRequest,
    CheckInResponse,
    CheckInUpdateRequest,
    PaginatedCheckInsResponse,
    PendingCheckInResponse,
)
from services.application_setting_service import ApplicationSettingService
from services.check_in_service import (
    CheckInDetail,
    CheckInEditWindowExpiredError,
    CheckInFieldsRequiredError,
    CheckInNotFoundError,
    CheckInService,
    ClientNotFoundError,
    DuplicateCheckInError,
    ForbiddenError,
    PendingCheckInDetail,
    SessionCancelledError,
    SessionNotFoundError,
    SessionNotStartedError,
    TrainerNotAssignedError,
    TrainerNotFoundError,
)

router = APIRouter(prefix="/api/v1/check-ins", tags=["check-ins"])


def get_check_in_repository(session: AsyncSession = Depends(get_db)) -> CheckInRepository:
    return SQLAlchemyCheckInRepository(session)


def get_client_repository(session: AsyncSession = Depends(get_db)) -> ClientRepository:
    return SQLAlchemyClientRepository(session)


def get_assignment_repository(
    session: AsyncSession = Depends(get_db),
) -> AssignmentRepository:
    return SQLAlchemyAssignmentRepository(session)


def get_session_repository(session: AsyncSession = Depends(get_db)) -> SessionRepository:
    return SQLAlchemySessionRepository(session)


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


def get_check_in_service(
    check_in_repository: CheckInRepository = Depends(get_check_in_repository),
    client_repository: ClientRepository = Depends(get_client_repository),
    assignment_repository: AssignmentRepository = Depends(get_assignment_repository),
    session_repository: SessionRepository = Depends(get_session_repository),
    application_setting_service: ApplicationSettingService = Depends(
        get_application_setting_service
    ),
) -> CheckInService:
    return CheckInService(
        check_in_repository,
        client_repository,
        assignment_repository,
        session_repository,
        application_setting_service,
    )


def _to_response(detail: CheckInDetail) -> CheckInResponse:
    return CheckInResponse(
        id=detail.id,
        session_id=detail.session_id,
        client_id=detail.client_id,
        sleep_hours=detail.sleep_hours,
        water_intake_liters=detail.water_intake_liters,
        energy_level=detail.energy_level,
        mood=detail.mood,
        workout_completed=detail.workout_completed,
        diet_followed=detail.diet_followed,
        notes=detail.notes,
        submitted_by=detail.submitted_by,
        submitted_at=detail.submitted_at,
        created_at=detail.created_at,
        updated_at=detail.updated_at,
    )


def _to_pending_response(detail: PendingCheckInDetail) -> PendingCheckInResponse:
    return PendingCheckInResponse(
        session_id=detail.session_id,
        client_id=detail.client_id,
        client_name=detail.client_name,
        scheduled_start=detail.scheduled_start,
        days_pending=detail.days_pending,
    )


@router.post("", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
async def create_check_in(
    payload: CheckInCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    check_in_service: CheckInService = Depends(get_check_in_service),
) -> CheckInResponse:
    try:
        detail = await check_in_service.create_check_in(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            session_id=payload.session_id,
            sleep_hours=payload.sleep_hours,
            water_intake_liters=payload.water_intake_liters,
            energy_level=payload.energy_level,
            mood=payload.mood,
            workout_completed=payload.workout_completed,
            diet_followed=payload.diet_followed,
            notes=payload.notes,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (SessionNotFoundError, TrainerNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TrainerNotAssignedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except CheckInFieldsRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except (SessionCancelledError, SessionNotStartedError, DuplicateCheckInError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_response(detail)


@router.get("", response_model=PaginatedCheckInsResponse, status_code=status.HTTP_200_OK)
async def list_check_ins(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    check_in_service: CheckInService = Depends(get_check_in_service),
) -> PaginatedCheckInsResponse:
    try:
        result = await check_in_service.list_check_ins(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            page=page,
            page_size=page_size,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (ClientNotFoundError, TrainerNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    total_pages = (result.total + page_size - 1) // page_size if result.total else 0
    return PaginatedCheckInsResponse(
        items=[_to_response(detail) for detail in result.items],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        total_pages=total_pages,
    )


@router.get("/pending", response_model=list[PendingCheckInResponse], status_code=status.HTTP_200_OK)
async def list_pending_check_ins(
    current_user: CurrentUser = Depends(get_current_user),
    check_in_service: CheckInService = Depends(get_check_in_service),
) -> list[PendingCheckInResponse]:
    try:
        items = await check_in_service.list_pending_check_ins(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TrainerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [_to_pending_response(item) for item in items]


@router.get(
    "/session/{session_id}",
    response_model=CheckInResponse,
    status_code=status.HTTP_200_OK,
)
async def get_check_in_by_session(
    session_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    check_in_service: CheckInService = Depends(get_check_in_service),
) -> CheckInResponse:
    try:
        detail = await check_in_service.get_check_in_by_session(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            session_id=session_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (SessionNotFoundError, CheckInNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)


@router.get(
    "/client/{client_id}",
    response_model=list[CheckInResponse],
    status_code=status.HTTP_200_OK,
)
async def get_client_check_ins(
    client_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    check_in_service: CheckInService = Depends(get_check_in_service),
) -> list[CheckInResponse]:
    try:
        items = await check_in_service.get_client_check_ins(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            client_id=client_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [_to_response(item) for item in items]


@router.get("/{check_in_id}", response_model=CheckInResponse, status_code=status.HTTP_200_OK)
async def get_check_in(
    check_in_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    check_in_service: CheckInService = Depends(get_check_in_service),
) -> CheckInResponse:
    try:
        detail = await check_in_service.get_check_in(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            check_in_id=check_in_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except CheckInNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)


@router.patch("/{check_in_id}", response_model=CheckInResponse, status_code=status.HTTP_200_OK)
async def update_check_in(
    check_in_id: uuid.UUID,
    payload: CheckInUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    check_in_service: CheckInService = Depends(get_check_in_service),
) -> CheckInResponse:
    try:
        detail = await check_in_service.update_check_in(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            check_in_id=check_in_id,
            values=payload.model_dump(exclude_unset=True),
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except CheckInNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CheckInFieldsRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except CheckInEditWindowExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_response(detail)
