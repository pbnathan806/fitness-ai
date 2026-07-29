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
    pending_check_ins: int
    clients_missing_check_ins_today: int


class ClientDashboardResponse(BaseModel):
    completed_check_ins: int
    expected_check_ins: int
    adherence_percentage: int
