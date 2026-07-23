from pydantic import BaseModel


class TrainerDashboardResponse(BaseModel):
    assigned_clients: int
    active_clients: int
    sessions_today: int
    upcoming_sessions_next_7_days: int
    pending_check_ins: int
    pending_measurements: int


class SuperAdminDashboardResponse(BaseModel):
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


class ClientDashboardResponse(BaseModel):
    check_ins_this_week: int
    target_check_ins: int | None
    check_in_adherence_percentage: int
