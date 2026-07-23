from fastapi import APIRouter, Depends, HTTPException, status
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
from repositories.dashboard_repository import (
    DashboardRepository,
    SQLAlchemyDashboardRepository,
)
from repositories.measurement_repository import (
    MeasurementRepository,
    SQLAlchemyMeasurementRepository,
)
from repositories.session_repository import SessionRepository, SQLAlchemySessionRepository
from repositories.subscription_repository import (
    SQLAlchemySubscriptionRepository,
    SubscriptionRepository,
)
from schemas.dashboard import (
    ClientDashboardResponse,
    SuperAdminDashboardResponse,
    TrainerDashboardResponse,
)
from services.application_setting_service import ApplicationSettingService
from services.dashboard_service import (
    ClientDashboard,
    ClientProfileNotFoundError,
    DashboardService,
    ForbiddenError,
    SuperAdminDashboard,
    TrainerDashboard,
    TrainerProfileNotFoundError,
)

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


def get_dashboard_repository(session: AsyncSession = Depends(get_db)) -> DashboardRepository:
    return SQLAlchemyDashboardRepository(session)


def get_client_repository(session: AsyncSession = Depends(get_db)) -> ClientRepository:
    return SQLAlchemyClientRepository(session)


def get_assignment_repository(
    session: AsyncSession = Depends(get_db),
) -> AssignmentRepository:
    return SQLAlchemyAssignmentRepository(session)


def get_session_repository(session: AsyncSession = Depends(get_db)) -> SessionRepository:
    return SQLAlchemySessionRepository(session)


def get_check_in_repository(session: AsyncSession = Depends(get_db)) -> CheckInRepository:
    return SQLAlchemyCheckInRepository(session)


def get_measurement_repository(
    session: AsyncSession = Depends(get_db),
) -> MeasurementRepository:
    return SQLAlchemyMeasurementRepository(session)


def get_subscription_repository(
    session: AsyncSession = Depends(get_db),
) -> SubscriptionRepository:
    return SQLAlchemySubscriptionRepository(session)


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


def get_dashboard_service(
    dashboard_repository: DashboardRepository = Depends(get_dashboard_repository),
    client_repository: ClientRepository = Depends(get_client_repository),
    assignment_repository: AssignmentRepository = Depends(get_assignment_repository),
    session_repository: SessionRepository = Depends(get_session_repository),
    check_in_repository: CheckInRepository = Depends(get_check_in_repository),
    measurement_repository: MeasurementRepository = Depends(get_measurement_repository),
    subscription_repository: SubscriptionRepository = Depends(get_subscription_repository),
    application_setting_service: ApplicationSettingService = Depends(
        get_application_setting_service
    ),
) -> DashboardService:
    return DashboardService(
        dashboard_repository,
        client_repository,
        assignment_repository,
        session_repository,
        check_in_repository,
        measurement_repository,
        subscription_repository,
        application_setting_service,
    )


def _to_trainer_response(detail: TrainerDashboard) -> TrainerDashboardResponse:
    return TrainerDashboardResponse(
        assigned_clients=detail.assigned_clients,
        active_clients=detail.active_clients,
        sessions_today=detail.sessions_today,
        upcoming_sessions_next_7_days=detail.upcoming_sessions_next_7_days,
        pending_check_ins=detail.pending_check_ins,
        pending_measurements=detail.pending_measurements,
    )


def _to_super_admin_response(detail: SuperAdminDashboard) -> SuperAdminDashboardResponse:
    return SuperAdminDashboardResponse(
        total_clients=detail.total_clients,
        active_clients=detail.active_clients,
        expired_clients=detail.expired_clients,
        inactive_clients=detail.inactive_clients,
        total_trainers=detail.total_trainers,
        sessions_today=detail.sessions_today,
        upcoming_sessions_next_7_days=detail.upcoming_sessions_next_7_days,
        measurements_recorded_this_month=detail.measurements_recorded_this_month,
        check_ins_submitted_today=detail.check_ins_submitted_today,
        clients_missing_check_ins_today=detail.clients_missing_check_ins_today,
    )


def _to_client_response(detail: ClientDashboard) -> ClientDashboardResponse:
    return ClientDashboardResponse(
        check_ins_this_week=detail.check_ins_this_week,
        target_check_ins=detail.target_check_ins,
        check_in_adherence_percentage=detail.check_in_adherence_percentage,
    )


@router.get("/trainer", response_model=TrainerDashboardResponse, status_code=status.HTTP_200_OK)
async def get_trainer_dashboard(
    current_user: CurrentUser = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> TrainerDashboardResponse:
    try:
        detail = await dashboard_service.get_trainer_dashboard(
            actor_role=current_user.active_role, actor_id=current_user.user_id
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TrainerProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_trainer_response(detail)


@router.get(
    "/super-admin", response_model=SuperAdminDashboardResponse, status_code=status.HTTP_200_OK
)
async def get_super_admin_dashboard(
    current_user: CurrentUser = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> SuperAdminDashboardResponse:
    try:
        detail = await dashboard_service.get_super_admin_dashboard(
            actor_role=current_user.active_role
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return _to_super_admin_response(detail)


@router.get("/client", response_model=ClientDashboardResponse, status_code=status.HTTP_200_OK)
async def get_client_dashboard(
    current_user: CurrentUser = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> ClientDashboardResponse:
    try:
        detail = await dashboard_service.get_client_dashboard(
            actor_role=current_user.active_role, actor_id=current_user.user_id
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ClientProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_client_response(detail)
