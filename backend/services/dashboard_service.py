import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.constants import RoleName
from repositories.assignment_repository import AssignmentRepository
from repositories.check_in_repository import CheckInRepository
from repositories.client_repository import ClientRepository
from repositories.dashboard_repository import DashboardRepository
from repositories.measurement_repository import MeasurementRepository
from repositories.session_repository import SessionRepository
from repositories.subscription_repository import SubscriptionRepository
from services.application_setting_service import ApplicationSettingService
from utils.dashboard import (
    classify_client_state,
    client_last_n_days_range_utc,
    client_week_range_utc,
    is_measurement_overdue,
    ist_month_range_utc,
    ist_next_days_range_utc,
    ist_today_range_utc,
)
from utils.subscription import current_india_date

_ADHERENCE_WINDOW_DAYS = 90


class ForbiddenError(Exception):
    """Raised when the acting user's role does not permit the requested action."""


class TrainerProfileNotFoundError(Exception):
    """Raised when no trainer profile exists for the acting user."""


class ClientProfileNotFoundError(Exception):
    """Raised when no client profile exists for the acting user."""


@dataclass(frozen=True)
class TrainerDashboard:
    assigned_clients: int
    active_clients: int
    sessions_today: int
    upcoming_sessions_next_7_days: int
    pending_check_ins: int
    pending_measurements: int


@dataclass(frozen=True)
class SuperAdminDashboard:
    total_clients: int
    active_clients: int
    expired_clients: int
    inactive_clients: int
    total_trainers: int
    sessions_today: int
    upcoming_sessions_next_7_days: int
    measurements_recorded_this_month: int
    check_ins_submitted_today: int
    clients_missing_check_ins_today: int


@dataclass(frozen=True)
class ClientDashboard:
    check_ins_this_week: int
    target_check_ins: int | None
    check_in_adherence_percentage: int


class DashboardService:
    """Read-only aggregate dashboards for the three Version-1 roles (Task-21).

    Client-state (ACTIVE/EXPIRED/INACTIVE) and measurement-overdue
    calculations read their thresholds from ApplicationSettingService
    (Task-20) instead of hardcoding them, per the acceptance criteria of
    both tasks. Trainer and Super Admin day/week/month boundaries are framed
    in Asia/Kolkata (TIMEZONE_REQUIREMENTS.md); the Client dashboard's
    boundaries are framed in that client's own timezone.
    """

    def __init__(
        self,
        dashboard_repository: DashboardRepository,
        client_repository: ClientRepository,
        assignment_repository: AssignmentRepository,
        session_repository: SessionRepository,
        check_in_repository: CheckInRepository,
        measurement_repository: MeasurementRepository,
        subscription_repository: SubscriptionRepository,
        application_setting_service: ApplicationSettingService,
    ) -> None:
        self._dashboard_repository = dashboard_repository
        self._client_repository = client_repository
        self._assignment_repository = assignment_repository
        self._session_repository = session_repository
        self._check_in_repository = check_in_repository
        self._measurement_repository = measurement_repository
        self._subscription_repository = subscription_repository
        self._application_setting_service = application_setting_service

    async def get_trainer_dashboard(
        self, actor_role: str | None, actor_id: uuid.UUID
    ) -> TrainerDashboard:
        if actor_role != RoleName.TRAINER:
            raise ForbiddenError("Only Trainers may view the trainer dashboard.")

        trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
        if trainer_id is None:
            raise TrainerProfileNotFoundError("No trainer profile exists for the current user.")

        assigned = await self._assignment_repository.list_clients_for_trainer(trainer_id)
        client_ids = [record.client.id for record in assigned]

        today = current_india_date()
        today_start, today_end = ist_today_range_utc()
        week_start, week_end = ist_next_days_range_utc(7)
        now = datetime.now(timezone.utc)

        subscription_expired_days = await self._application_setting_service.get_int(
            "subscription_expired_days"
        )
        measurement_overdue_days = await self._application_setting_service.get_int(
            "measurement_overdue_days"
        )

        end_dates = await self._subscription_repository.get_latest_end_dates_for_clients(
            client_ids
        )
        active_clients = sum(
            1
            for client_id in client_ids
            if classify_client_state(end_dates.get(client_id), today, subscription_expired_days)
            == "ACTIVE"
        )

        latest_measurements = await self._measurement_repository.get_latest_recorded_at_for_clients(
            client_ids
        )
        pending_measurements = sum(
            1
            for client_id in client_ids
            if is_measurement_overdue(
                latest_measurements.get(client_id), today, measurement_overdue_days
            )
        )

        sessions_today = await self._session_repository.count_in_range(
            today_start, today_end, trainer_id=trainer_id, exclude_cancelled=True
        )
        upcoming_sessions_next_7_days = await self._session_repository.count_in_range(
            week_start, week_end, trainer_id=trainer_id, exclude_cancelled=True
        )
        pending_check_ins = await self._dashboard_repository.count_pending_check_ins(
            client_ids, today_start, today_end, now
        )

        return TrainerDashboard(
            assigned_clients=len(client_ids),
            active_clients=active_clients,
            sessions_today=sessions_today,
            upcoming_sessions_next_7_days=upcoming_sessions_next_7_days,
            pending_check_ins=pending_check_ins,
            pending_measurements=pending_measurements,
        )

    async def get_super_admin_dashboard(self, actor_role: str | None) -> SuperAdminDashboard:
        if actor_role != RoleName.SUPER_ADMIN:
            raise ForbiddenError("Only Super Admins may view the super admin dashboard.")

        today = current_india_date()
        today_start, today_end = ist_today_range_utc()
        week_start, week_end = ist_next_days_range_utc(7)
        month_start, month_end = ist_month_range_utc()
        now = datetime.now(timezone.utc)

        subscription_expired_days = await self._application_setting_service.get_int(
            "subscription_expired_days"
        )

        total_clients = await self._client_repository.count_all()
        total_trainers = await self._dashboard_repository.count_total_trainers()

        end_dates = await self._subscription_repository.get_latest_end_dates_for_clients(None)
        active_clients = expired_clients = inactive_clients = 0
        for end_date in end_dates.values():
            state = classify_client_state(end_date, today, subscription_expired_days)
            if state == "ACTIVE":
                active_clients += 1
            elif state == "EXPIRED":
                expired_clients += 1
            elif state == "INACTIVE":
                inactive_clients += 1

        sessions_today = await self._session_repository.count_in_range(
            today_start, today_end, exclude_cancelled=True
        )
        upcoming_sessions_next_7_days = await self._session_repository.count_in_range(
            week_start, week_end, exclude_cancelled=True
        )
        measurements_recorded_this_month = await self._measurement_repository.count_in_range(
            month_start, month_end
        )
        check_ins_submitted_today = await self._check_in_repository.count_in_range(
            today_start, today_end
        )
        clients_missing_check_ins_today = await self._dashboard_repository.count_pending_check_ins(
            None, today_start, today_end, now
        )

        return SuperAdminDashboard(
            total_clients=total_clients,
            active_clients=active_clients,
            expired_clients=expired_clients,
            inactive_clients=inactive_clients,
            total_trainers=total_trainers,
            sessions_today=sessions_today,
            upcoming_sessions_next_7_days=upcoming_sessions_next_7_days,
            measurements_recorded_this_month=measurements_recorded_this_month,
            check_ins_submitted_today=check_ins_submitted_today,
            clients_missing_check_ins_today=clients_missing_check_ins_today,
        )

    async def get_client_dashboard(
        self, actor_role: str | None, actor_id: uuid.UUID
    ) -> ClientDashboard:
        if actor_role != RoleName.CLIENT:
            raise ForbiddenError("Only Clients may view the client dashboard.")

        client_record = await self._client_repository.get_by_user_id(actor_id)
        if client_record is None:
            raise ClientProfileNotFoundError("No client profile exists for the current user.")

        client = client_record.client
        week_start, week_end = client_week_range_utc(client.timezone)
        window_start, window_end = client_last_n_days_range_utc(
            client.timezone, _ADHERENCE_WINDOW_DAYS
        )

        check_ins_this_week = await self._check_in_repository.count_in_range(
            week_start, week_end, client_ids=[client.id]
        )

        latest_subscription = await self._subscription_repository.get_latest_for_client(client.id)
        target_check_ins = (
            latest_subscription.plan_sessions_per_week if latest_subscription else None
        )

        submitted_check_ins = await self._check_in_repository.count_in_range(
            window_start, window_end, client_ids=[client.id]
        )
        expected_check_ins = await self._session_repository.count_in_range(
            window_start, window_end, client_id=client.id, exclude_cancelled=True
        )
        adherence_percentage = (
            round(submitted_check_ins / expected_check_ins * 100) if expected_check_ins > 0 else 0
        )

        return ClientDashboard(
            check_ins_this_week=check_ins_this_week,
            target_check_ins=target_check_ins,
            check_in_adherence_percentage=adherence_percentage,
        )
