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
from repositories.dashboard_repository import (
    DashboardRepository,
    SQLAlchemyDashboardRepository,
)
from repositories.physical_assessment_repository import (
    PhysicalAssessmentRepository,
    SQLAlchemyPhysicalAssessmentRepository,
)
from repositories.role_repository import RoleRepository, SQLAlchemyRoleRepository
from repositories.session_repository import SessionRepository, SQLAlchemySessionRepository
from repositories.trainer_availability_repository import (
    SQLAlchemyTrainerAvailabilityRepository,
    TrainerAvailabilityRepository,
)
from repositories.trainer_repository import SQLAlchemyTrainerRepository, TrainerRepository
from repositories.user_repository import SQLAlchemyUserRepository, UserRepository
from schemas.trainer import (
    PaginatedTrainersResponse,
    TrainerAvailabilityRequest,
    TrainerAvailabilityResponse,
    TrainerCreateRequest,
    TrainerCreateResponse,
    TrainerPerformanceResponse,
    TrainerResponse,
    TrainerSelfUpdateRequest,
    TrainerStatusUpdateRequest,
    TrainerSummaryResponse,
    TrainerUpdateRequest,
)
from services.application_setting_service import ApplicationSettingService
from services.trainer_service import (
    AvailabilityNotFoundError,
    AvailabilityOverlapError,
    ForbiddenError,
    InvalidAvailabilityError,
    TrainerAlreadyExistsError,
    TrainerAvailabilityDetail,
    TrainerCreated,
    TrainerNotFoundError,
    TrainerPerformance,
    TrainerProfileDetail,
    TrainerService,
    TrainerSummary,
)

router = APIRouter(prefix="/api/v1/trainers", tags=["trainers"])


def get_trainer_repository(session: AsyncSession = Depends(get_db)) -> TrainerRepository:
    return SQLAlchemyTrainerRepository(session)


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return SQLAlchemyUserRepository(session)


def get_role_repository(session: AsyncSession = Depends(get_db)) -> RoleRepository:
    return SQLAlchemyRoleRepository(session)


def get_assignment_repository(session: AsyncSession = Depends(get_db)) -> AssignmentRepository:
    return SQLAlchemyAssignmentRepository(session)


def get_session_repository(session: AsyncSession = Depends(get_db)) -> SessionRepository:
    return SQLAlchemySessionRepository(session)


def get_check_in_repository(session: AsyncSession = Depends(get_db)) -> CheckInRepository:
    return SQLAlchemyCheckInRepository(session)


def get_physical_assessment_repository(
    session: AsyncSession = Depends(get_db),
) -> PhysicalAssessmentRepository:
    return SQLAlchemyPhysicalAssessmentRepository(session)


def get_trainer_availability_repository(
    session: AsyncSession = Depends(get_db),
) -> TrainerAvailabilityRepository:
    return SQLAlchemyTrainerAvailabilityRepository(session)


def get_dashboard_repository(session: AsyncSession = Depends(get_db)) -> DashboardRepository:
    return SQLAlchemyDashboardRepository(session)


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


def get_trainer_service(
    trainer_repository: TrainerRepository = Depends(get_trainer_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    role_repository: RoleRepository = Depends(get_role_repository),
    assignment_repository: AssignmentRepository = Depends(get_assignment_repository),
    session_repository: SessionRepository = Depends(get_session_repository),
    check_in_repository: CheckInRepository = Depends(get_check_in_repository),
    physical_assessment_repository: PhysicalAssessmentRepository = Depends(
        get_physical_assessment_repository
    ),
    trainer_availability_repository: TrainerAvailabilityRepository = Depends(
        get_trainer_availability_repository
    ),
    dashboard_repository: DashboardRepository = Depends(get_dashboard_repository),
    application_setting_service: ApplicationSettingService = Depends(
        get_application_setting_service
    ),
) -> TrainerService:
    return TrainerService(
        trainer_repository,
        user_repository,
        role_repository,
        assignment_repository,
        session_repository,
        check_in_repository,
        physical_assessment_repository,
        trainer_availability_repository,
        dashboard_repository,
        application_setting_service,
    )


def _to_response(detail: TrainerProfileDetail) -> TrainerResponse:
    return TrainerResponse(
        id=detail.id,
        first_name=detail.first_name,
        last_name=detail.last_name,
        email=detail.email,
        phone_number=detail.phone_number,
        timezone=detail.timezone,
        is_active=detail.is_active,
        created_at=detail.created_at,
        updated_at=detail.updated_at,
    )


def _to_summary_response(summary: TrainerSummary) -> TrainerSummaryResponse:
    return TrainerSummaryResponse(
        assigned_clients=summary.assigned_clients,
        sessions_this_week=summary.sessions_this_week,
        completed_sessions_this_month=summary.completed_sessions_this_month,
        pending_check_ins=summary.pending_check_ins,
        pending_physical_assessments=summary.pending_physical_assessments,
    )


def _to_performance_response(performance: TrainerPerformance) -> TrainerPerformanceResponse:
    return TrainerPerformanceResponse(
        assigned_clients=performance.assigned_clients,
        completed_sessions=performance.completed_sessions,
        completion_rate=performance.completion_rate,
        average_check_in_rate=performance.average_check_in_rate,
    )


def _to_availability_response(
    detail: TrainerAvailabilityDetail,
) -> TrainerAvailabilityResponse:
    return TrainerAvailabilityResponse(
        id=detail.id,
        trainer_id=detail.trainer_id,
        weekday=detail.weekday,
        start_time=detail.start_time,
        end_time=detail.end_time,
        is_available=detail.is_available,
        created_at=detail.created_at,
    )


@router.post("", response_model=TrainerCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_trainer(
    payload: TrainerCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    trainer_service: TrainerService = Depends(get_trainer_service),
) -> TrainerCreateResponse:
    try:
        created: TrainerCreated = await trainer_service.create_trainer(
            actor_role=current_user.active_role,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            phone_number=payload.phone_number,
            timezone=payload.timezone,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TrainerAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return TrainerCreateResponse(
        id=created.trainer.id, temporary_password=created.temporary_password
    )


@router.get("/me", response_model=TrainerResponse, status_code=status.HTTP_200_OK)
async def get_current_trainer(
    current_user: CurrentUser = Depends(get_current_user),
    trainer_service: TrainerService = Depends(get_trainer_service),
) -> TrainerResponse:
    try:
        detail = await trainer_service.get_self(
            actor_role=current_user.active_role, actor_id=current_user.user_id
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TrainerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)


@router.put("/me", response_model=TrainerResponse, status_code=status.HTTP_200_OK)
async def update_current_trainer(
    payload: TrainerSelfUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    trainer_service: TrainerService = Depends(get_trainer_service),
) -> TrainerResponse:
    try:
        detail = await trainer_service.update_self(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            phone_number=payload.phone_number,
            timezone=payload.timezone,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TrainerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)


@router.get(
    "/me/availability",
    response_model=list[TrainerAvailabilityResponse],
    status_code=status.HTTP_200_OK,
)
async def list_current_trainer_availability(
    current_user: CurrentUser = Depends(get_current_user),
    trainer_service: TrainerService = Depends(get_trainer_service),
) -> list[TrainerAvailabilityResponse]:
    try:
        slots = await trainer_service.list_availability(
            actor_role=current_user.active_role, actor_id=current_user.user_id
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TrainerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [_to_availability_response(slot) for slot in slots]


@router.post(
    "/me/availability",
    response_model=TrainerAvailabilityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_current_trainer_availability(
    payload: TrainerAvailabilityRequest,
    current_user: CurrentUser = Depends(get_current_user),
    trainer_service: TrainerService = Depends(get_trainer_service),
) -> TrainerAvailabilityResponse:
    try:
        detail = await trainer_service.create_availability(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            weekday=payload.weekday,
            start_time=payload.start_time,
            end_time=payload.end_time,
            is_available=payload.is_available,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TrainerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidAvailabilityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except AvailabilityOverlapError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_availability_response(detail)


@router.put(
    "/me/availability/{availability_id}",
    response_model=TrainerAvailabilityResponse,
    status_code=status.HTTP_200_OK,
)
async def update_current_trainer_availability(
    availability_id: uuid.UUID,
    payload: TrainerAvailabilityRequest,
    current_user: CurrentUser = Depends(get_current_user),
    trainer_service: TrainerService = Depends(get_trainer_service),
) -> TrainerAvailabilityResponse:
    try:
        detail = await trainer_service.update_availability(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            availability_id=availability_id,
            weekday=payload.weekday,
            start_time=payload.start_time,
            end_time=payload.end_time,
            is_available=payload.is_available,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (TrainerNotFoundError, AvailabilityNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidAvailabilityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except AvailabilityOverlapError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_availability_response(detail)


@router.delete("/me/availability/{availability_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_trainer_availability(
    availability_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    trainer_service: TrainerService = Depends(get_trainer_service),
) -> None:
    try:
        await trainer_service.delete_availability(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            availability_id=availability_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (TrainerNotFoundError, AvailabilityNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{trainer_id}", response_model=TrainerResponse, status_code=status.HTTP_200_OK)
async def get_trainer(
    trainer_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    trainer_service: TrainerService = Depends(get_trainer_service),
) -> TrainerResponse:
    try:
        detail = await trainer_service.get_trainer(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            trainer_id=trainer_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TrainerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)


@router.get(
    "/{trainer_id}/availability",
    response_model=list[TrainerAvailabilityResponse],
    status_code=status.HTTP_200_OK,
)
async def get_trainer_availability(
    trainer_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    trainer_service: TrainerService = Depends(get_trainer_service),
) -> list[TrainerAvailabilityResponse]:
    try:
        slots = await trainer_service.get_availability(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            trainer_id=trainer_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TrainerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [_to_availability_response(slot) for slot in slots]


@router.put("/{trainer_id}", response_model=TrainerResponse, status_code=status.HTTP_200_OK)
async def update_trainer(
    trainer_id: uuid.UUID,
    payload: TrainerUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    trainer_service: TrainerService = Depends(get_trainer_service),
) -> TrainerResponse:
    try:
        detail = await trainer_service.update_trainer(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            trainer_id=trainer_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone_number=payload.phone_number,
            timezone=payload.timezone,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TrainerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)


@router.patch(
    "/{trainer_id}/status", response_model=TrainerResponse, status_code=status.HTTP_200_OK
)
async def update_trainer_status(
    trainer_id: uuid.UUID,
    payload: TrainerStatusUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    trainer_service: TrainerService = Depends(get_trainer_service),
) -> TrainerResponse:
    try:
        detail = await trainer_service.update_status(
            actor_role=current_user.active_role,
            trainer_id=trainer_id,
            is_active=payload.is_active,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TrainerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(detail)


@router.get(
    "/{trainer_id}/summary", response_model=TrainerSummaryResponse, status_code=status.HTTP_200_OK
)
async def get_trainer_summary(
    trainer_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    trainer_service: TrainerService = Depends(get_trainer_service),
) -> TrainerSummaryResponse:
    try:
        summary = await trainer_service.get_summary(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            trainer_id=trainer_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TrainerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_summary_response(summary)


@router.get(
    "/{trainer_id}/performance",
    response_model=TrainerPerformanceResponse,
    status_code=status.HTTP_200_OK,
)
async def get_trainer_performance(
    trainer_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    trainer_service: TrainerService = Depends(get_trainer_service),
) -> TrainerPerformanceResponse:
    try:
        performance = await trainer_service.get_performance(
            actor_role=current_user.active_role,
            actor_id=current_user.user_id,
            trainer_id=trainer_id,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TrainerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_performance_response(performance)


@router.get("", response_model=PaginatedTrainersResponse, status_code=status.HTTP_200_OK)
async def list_trainers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    first_name: str | None = Query(default=None),
    last_name: str | None = Query(default=None),
    email: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    sort_by: str = Query(default="created_at", pattern="^(created_at|first_name)$"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    current_user: CurrentUser = Depends(get_current_user),
    trainer_service: TrainerService = Depends(get_trainer_service),
) -> PaginatedTrainersResponse:
    try:
        result = await trainer_service.list_trainers(
            actor_role=current_user.active_role,
            page=page,
            page_size=page_size,
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_active=is_active,
            sort_by=sort_by,
            sort_desc=(sort_dir == "desc"),
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    total_pages = (result.total + page_size - 1) // page_size if result.total else 0
    return PaginatedTrainersResponse(
        items=[_to_response(detail) for detail in result.items],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        total_pages=total_pages,
    )
